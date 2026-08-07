"""
ToolManager — central gatekeeper for all tool access.

Agents must NEVER import or instantiate tools directly.
All tool execution must flow through ToolManager.

This central manager provides:
- A registry of available tools.
- Permission checking before execution.
- Standardized execution results.
- Comprehensive logging of every tool call.

By routing all tool access here, we enforce a single
chokepoint where we can add security, rate-limiting,
sandboxing, and audit logging in the future.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.logger import setup_logger

logger = setup_logger(__name__)


class ToolResult:
    """
    Standardized return type for every tool execution.

    All tool calls return a ToolResult so callers never
    have to handle heterogeneous return types.

    Attributes:
        success:   True if the tool ran without error.
        tool_name: The name of the tool that was executed.
        output:    The primary output data (string, list, dict, etc.).
        error:     Error message if success is False.
        metadata:  Arbitrary extra information (e.g. exit codes, file sizes).
    """

    def __init__(
        self,
        success: bool,
        tool_name: str,
        output: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        self.success   = success
        self.tool_name = tool_name
        self.output    = output
        self.error     = error
        self.metadata  = metadata or {}

    def __repr__(self) -> str:
        return (
            f"ToolResult(tool={self.tool_name}, success={self.success}, "
            f"output={str(self.output)[:60]!r})"
        )


class ToolManager:
    """
    Central manager and registry for all application tools.

    All agents and engine components must call `execute_tool()`
    on this manager rather than importing tools directly.

    Usage:
        tool_manager = ToolManager()
        tool_manager.register_tool("file", FileTool(workspace_root="..."))
        result = tool_manager.execute_tool("file", action="read", path="main.py")

    Future enhancements (TODO):
        - Auto-discover and register tools from ai/tools/ at startup.
        - Per-tool permission scopes (read-only, write, network).
        - Usage quotas and rate limiting.
        - Sandboxed execution environment.
    """

    def __init__(self) -> None:
        # Registry maps tool name → tool instance
        self._registry: Dict[str, Any] = {}
        logger.info("ToolManager initialized with empty registry.")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_tool(self, name: str, tool_instance: Any) -> None:
        """
        Register a tool with the manager.

        Args:
            name:          The canonical name for this tool (e.g. "file", "git").
            tool_instance: An instance of a BaseTool subclass.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if name in self._registry:
            raise ValueError(
                f"A tool named '{name}' is already registered. "
                f"Unregister it first before replacing."
            )
        self._registry[name] = tool_instance
        logger.info(f"Tool registered: '{name}' ({type(tool_instance).__name__})")

    def unregister_tool(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name not in self._registry:
            logger.warning(f"Attempted to unregister unknown tool: '{name}'")
            return
        del self._registry[name]
        logger.info(f"Tool unregistered: '{name}'")

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def is_available(self, name: str) -> bool:
        """Return True if a tool with this name is registered."""
        return name in self._registry

    def list_tools(self) -> list[str]:
        """Return the names of all currently registered tools."""
        return list(self._registry.keys())

    def get_tool(self, name: str) -> Any:
        """
        Retrieve a tool instance by name.

        Prefer `execute_tool()` for actual calls. Use this only
        when you need direct access to the instance (e.g. for config).

        Raises:
            KeyError: If no tool with the given name is registered.
        """
        if name not in self._registry:
            raise KeyError(f"Tool '{name}' is not registered. Available: {self.list_tools()}")
        return self._registry[name]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute_tool(self, name: str, action: str, **kwargs: Any) -> ToolResult:
        """
        Execute a registered tool action and return a standardized result.

        Args:
            name:   The registered name of the tool to use.
            action: The method name to call on the tool instance.
            **kwargs: Arguments forwarded to the tool method.

        Returns:
            ToolResult with success/failure state and output.

        TODO:
            - Add permission checks before execution.
            - Emit EventBus events for tool start/complete.
            - Add timeout enforcement.
        """
        logger.info(f"Executing tool: '{name}' | action: '{action}' | args: {kwargs}")

        if self._requires_confirmation(name, action) and not kwargs.get("confirm", False):
            msg = (
                f"Tool '{name}.{action}' requires explicit confirmation before proceeding. "
                f"Retry with confirm=True after verifying the target."
            )
            logger.warning(msg)
            return ToolResult(
                success=False,
                tool_name=name,
                error=msg,
                metadata={
                    "requires_confirmation": True,
                    "tool": name,
                    "action": action,
                },
            )

        # Permission check placeholder
        if not self._check_permissions(name, action):
            msg = f"Permission denied for tool '{name}' action '{action}'."
            logger.warning(msg)
            return ToolResult(success=False, tool_name=name, error=msg)

        # Tool availability check
        if not self.is_available(name):
            msg = f"Tool '{name}' is not registered. Available tools: {self.list_tools()}"
            logger.error(msg)
            return ToolResult(success=False, tool_name=name, error=msg)

        tool = self._registry[name]

        # Validate that the requested action exists on the tool
        if not hasattr(tool, action) or not callable(getattr(tool, action)):
            msg = f"Tool '{name}' has no callable action '{action}'."
            logger.error(msg)
            return ToolResult(success=False, tool_name=name, error=msg)

        # Execute the action
        try:
            method = getattr(tool, action)
            output = method(**kwargs)
            logger.info(f"Tool '{name}.{action}' succeeded.")
            return ToolResult(success=True, tool_name=name, output=output)
        except Exception as exc:
            logger.error(f"Tool '{name}.{action}' raised an exception: {exc}", exc_info=True)
            return ToolResult(success=False, tool_name=name, error=str(exc))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _check_permissions(self, tool_name: str, action: str) -> bool:
        """
        Validate that the requested action is permitted.

        Currently always returns True (open permissions).

        TODO:
            - Implement per-tool, per-action permission scopes.
            - Integrate with a user-configurable safety policy.
        """
        # TODO: Replace with real permission table
        return True

    def _requires_confirmation(self, tool_name: str, action: str) -> bool:
        """Return True for destructive actions that must be confirmed."""
        destructive_actions = {"delete", "delete_file"}
        if tool_name == "file" and action in destructive_actions:
            return True
        return False
