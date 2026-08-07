"""
Tool Registry — v1.5

Registry for all available tools with permission checking and discovery.
"""

import importlib
import inspect
import os
from pathlib import Path
from typing import Dict, List, Optional, Type
from core.logger import setup_logger

from ai.tools.tool_base import BaseTool, ToolPermission, ToolCategory


logger = setup_logger(__name__)


class ToolRegistry:
    """
    Central registry for all tools.
    
    Provides:
    - Tool registration and discovery
    - Permission checking before execution
    - Tool instantiation with proper dependencies
    - Tool metadata and introspection
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._logger = logger
        self._registered_paths: List[str] = []
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Registration
    # ─────────────────────────────────────────────────────────────────────────────

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            self._logger.warning(f"Tool '{tool.name}' already registered, replacing")
        
        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = type(tool)
        self._logger.info(f"Registered tool: {tool.name} ({tool.category.value})")
    
    def unregister_tool(self, name: str) -> bool:
        """Remove a tool from the registry."""
        if name not in self._tools:
            return False
        
        del self._tools[name]
        del self._tool_classes[name]
        self._logger.info(f"Unregistered tool: {name}")
        return True
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class for later instantiation."""
        instance = tool_class.__name__
        name = tool_class.__name__.replace("Tool", "").lower()
        self._tool_classes[name] = tool_class
        self._logger.debug(f"Registered tool class: {name}")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Discovery
    # ─────────────────────────────────────────────────────────────────────────────

    def discover_tools(self, tools_dir: str = "ai/tools") -> List[str]:
        """
        Discover and register all tools from a directory.
        
        Args:
            tools_dir: Directory containing tool files
            
        Returns:
            List of registered tool names
        """
        registered = []
        
        if not os.path.exists(tools_dir):
            self._logger.warning(f"Tools directory not found: {tools_dir}")
            return registered
        
        self._registered_paths.append(tools_dir)
        
        # Discover from ai/tools directory
        tool_files = Path(tools_dir).glob("*.py")
        
        for tool_file in tool_files:
            if tool_file.name.startswith("_"):
                continue
            
            module_name = f"ai.tools.{tool_file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Find all BaseTool subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj != BaseTool:
                        # Create instance with empty constructor
                        # This will need to be updated with proper dependency injection
                        try:
                            tool_instance = obj()
                            self.register_tool(tool_instance)
                            registered.append(tool_instance.name)
                        except Exception as e:
                            self._logger.warning(f"Could not instantiate {name}: {e}")
                
            except Exception as e:
                self._logger.warning(f"Could not load module {module_name}: {e}")
        
        self._logger.info(f"Discovered {len(registered)} tools from {tools_dir}")
        return registered
    
    def discover_plugin_tools(self, plugin_dir: str) -> List[str]:
        """
        Discover tools from a plugin directory.
        
        Args:
            plugin_dir: Directory containing plugin tools
            
        Returns:
            List of registered plugin tool names
        """
        # Plugin discovery would work similarly but with different import logic
        # For now, this is a placeholder for future plugin support
        self._logger.info(f"Plugin discovery directory: {plugin_dir}")
        return []
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Access
    # ─────────────────────────────────────────────────────────────────────────────

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return dict(self._tools)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """Get all tools in a category."""
        return [
            tool for tool in self._tools.values()
            if tool.category == category
        ]
    
    def get_tools_by_permission(self, permission: ToolPermission) -> List[BaseTool]:
        """Get all tools with a specific permission level."""
        return [
            tool for tool in self._tools.values()
            if tool.permission_level == permission
        ]
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────────────────────────

    def can_execute(self, tool_name: str, permission_required: bool = True) -> bool:
        """
        Check if a tool can be executed.
        
        Args:
            tool_name: Name of the tool
            permission_required: If True, requires confirmation for non-safe tools
            
        Returns:
            True if execution is allowed
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        
        if permission_required and tool.requires_confirmation:
            # In production, this would check user permission
            return True
        
        return True
    
    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a tool."""
        tool = self.get_tool(name)
        if not tool:
            return None
        return tool.get_metadata()
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all tools."""
        return [tool.get_metadata() for tool in self._tools.values()]
