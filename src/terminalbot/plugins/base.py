"""Base plugin class."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List


class BasePlugin(ABC):
    """
    Abstract base class for plugins.

    Plugins provide tools (commands) that can be used by the LLM
    or directly invoked in rule-based mode.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Plugin identifier.

        Returns:
            Unique plugin name
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Plugin description.

        Returns:
            Human-readable description of plugin capabilities
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of tools provided by this plugin.

        Each tool is a dict with:
        - name: Tool identifier
        - description: What the tool does
        - function: Callable that implements the tool
        - parameters: Dict describing function parameters

        Returns:
            List of tool definitions
        """
        pass

    def validate_command(self, command: str) -> bool:
        """
        Validate command before execution.

        Override this to add plugin-specific safety checks.

        Args:
            command: Command to validate

        Returns:
            True if command is safe to execute
        """
        return True

    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool definition or None if not found
        """
        for tool in self.get_tools():
            if tool["name"] == tool_name:
                return tool
        return None

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in plugin '{self.name}'")

        func = tool["function"]
        return func(**kwargs)


from typing import Optional  # noqa: E402 (import at end for forward reference)
