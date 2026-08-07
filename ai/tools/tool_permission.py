"""
Tool Permission System — v1.5

Permission checking and user confirmation for dangerous tools.
"""

from enum import Enum
from typing import Dict, List, Optional
from core.logger import setup_logger


logger = setup_logger(__name__)


class PermissionLevel(Enum):
    """Permission levels for tools."""
    SAFE = "safe"           # No user confirmation required
    WARNING = "warning"     # User confirmation required
    DANGEROUS = "dangerous" # User confirmation required, logged


class PermissionPolicy:
    """
    Defines the policy for tool permissions.
    
    In production, this would be loaded from a config file
    and allow users to customize permissions for each tool.
    """
    
    def __init__(self):
        self._policies: Dict[str, Dict[str, str]] = {}
        self._default_policy = PermissionLevel.SAFE
        self._logger = logger
        
        # Default policies
        self._default_policies = {
            # File operations
            "file.read_file": PermissionLevel.SAFE,
            "file.write_file": PermissionLevel.WARNING,
            "file.create_file": PermissionLevel.WARNING,
            "file.delete_file": PermissionLevel.DANGEROUS,
            "file.rename_file": PermissionLevel.WARNING,
            "file.move_file": PermissionLevel.WARNING,
            
            # Project operations
            "project.scan": PermissionLevel.SAFE,
            "project.analyze": PermissionLevel.SAFE,
            
            # Terminal operations
            "terminal.run_command": PermissionLevel.WARNING,
            "terminal.background_command": PermissionLevel.WARNING,
            "terminal.stop_command": PermissionLevel.SAFE,
            
            # Git operations
            "git.status": PermissionLevel.SAFE,
            "git.commit": PermissionLevel.WARNING,
            "git.branch": PermissionLevel.WARNING,
            "git.rollback": PermissionLevel.DANGEROUS,
            "git.snapshot": PermissionLevel.WARNING,
            
            # GitHub operations (disabled by default)
            "github.status": PermissionLevel.WARNING,
            "github.push": PermissionLevel.DANGEROUS,
            
            # Browser operations
            "browser.search": PermissionLevel.SAFE,
            
            # Verification operations
            "verification.run_tests": PermissionLevel.WARNING,
            "verification.run_build": PermissionLevel.WARNING,
            "verification.run_linter": PermissionLevel.SAFE,
            
            # Editor operations
            "editor.open_file": PermissionLevel.SAFE,
            "editor.focus_line": PermissionLevel.SAFE,
        }
        
        self._logger.info("PermissionPolicy initialized with default policies")
    
    def get_permission(self, tool_name: str, action: str) -> PermissionLevel:
        """
        Get the permission level for a tool action.
        
        Args:
            tool_name: Name of the tool
            action: Action being performed
            
        Returns:
            Permission level for the action
        """
        key = f"{tool_name}.{action}"
        
        # Check specific policy
        if key in self._policies:
            return PermissionLevel(self._policies[key])
        
        # Check default policy
        if key in self._default_policies:
            return self._default_policies[key]
        
        # Return default
        return self._default_policy
    
    def set_policy(self, tool_name: str, action: str, 
                   level: PermissionLevel) -> None:
        """
        Set a custom permission policy.
        
        Args:
            tool_name: Name of the tool
            action: Action being performed
            level: Permission level
        """
        key = f"{tool_name}.{action}"
        self._policies[key] = level.value
        self._logger.info(f"Set policy: {key} -> {level.value}")
    
    def requires_confirmation(self, tool_name: str, action: str) -> bool:
        """Check if a tool action requires user confirmation."""
        level = self.get_permission(tool_name, action)
        return level in (PermissionLevel.WARNING, PermissionLevel.DANGEROUS)
    
    def is_dangerous(self, tool_name: str, action: str) -> bool:
        """Check if a tool action is dangerous."""
        level = self.get_permission(tool_name, action)
        return level == PermissionLevel.DANGEROUS
    
    def get_dangerous_tools(self) -> List[str]:
        """Get list of all dangerous tool actions."""
        dangerous = []
        for key, level in self._default_policies.items():
            if level == PermissionLevel.DANGEROUS:
                dangerous.append(key)
        return dangerous
    
    def get_policy_summary(self) -> Dict[str, str]:
        """Get summary of all policies."""
        policies = dict(self._default_policies)
        policies.update(self._policies)
        return policies


# Global instance
_permission_policy = None


def get_permission_policy() -> PermissionPolicy:
    """Get the global permission policy."""
    global _permission_policy
    if _permission_policy is None:
        _permission_policy = PermissionPolicy()
    return _permission_policy


def reset_permission_policy():
    """Reset the global permission policy."""
    global _permission_policy
    _permission_policy = None
