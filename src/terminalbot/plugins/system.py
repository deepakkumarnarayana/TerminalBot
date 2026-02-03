"""System information plugin."""

import logging
from typing import Any, Dict, List

from ..executor import CommandExecutor
from .base import BasePlugin

logger = logging.getLogger(__name__)


class SystemPlugin(BasePlugin):
    """
    Plugin for system information queries.

    Provides tools for checking system status, disk space,
    memory usage, and other system metrics.
    """

    def __init__(self, executor: CommandExecutor = None):
        """
        Initialize system plugin.

        Args:
            executor: Command executor (creates one if None)
        """
        self.executor = executor or CommandExecutor()

    @property
    def name(self) -> str:
        """Plugin name."""
        return "system"

    @property
    def description(self) -> str:
        """Plugin description."""
        return "System information and metrics (uptime, disk, memory, OS version)"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of system info tools."""
        return [
            {
                "name": "get_system_info",
                "description": "Get comprehensive system information including OS, kernel, uptime",
                "function": self.get_system_info,
                "parameters": {},
            },
            {
                "name": "check_disk_space",
                "description": "Check disk space usage across all filesystems",
                "function": self.check_disk_space,
                "parameters": {},
            },
            {
                "name": "check_memory",
                "description": "Check memory (RAM) usage and availability",
                "function": self.check_memory,
                "parameters": {},
            },
            {
                "name": "get_uptime",
                "description": "Get system uptime and load averages",
                "function": self.get_uptime,
                "parameters": {},
            },
            {
                "name": "get_os_info",
                "description": "Get operating system and distribution information",
                "function": self.get_os_info,
                "parameters": {},
            },
        ]

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information.

        Returns:
            Dict with system details
        """
        # Run multiple commands
        uname_result = self.executor.execute_sync("uname -a")
        uptime_result = self.executor.execute_sync("uptime")

        return {
            "success": uname_result.success and uptime_result.success,
            "system": uname_result.stdout.strip() if uname_result.success else "Unknown",
            "uptime": uptime_result.stdout.strip() if uptime_result.success else "Unknown",
        }

    def check_disk_space(self) -> Dict[str, Any]:
        """
        Check disk space usage.

        Returns:
            Dict with disk usage information
        """
        result = self.executor.execute_sync("df -h")

        if not result.success:
            return {
                "success": False,
                "error": result.stderr,
            }

        return {
            "success": True,
            "output": result.stdout,
            "raw_output": result.stdout,
        }

    def check_memory(self) -> Dict[str, Any]:
        """
        Check memory usage.

        Returns:
            Dict with memory usage information
        """
        result = self.executor.execute_sync("free -h")

        if not result.success:
            return {
                "success": False,
                "error": result.stderr,
            }

        return {
            "success": True,
            "output": result.stdout,
            "raw_output": result.stdout,
        }

    def get_uptime(self) -> Dict[str, Any]:
        """
        Get system uptime.

        Returns:
            Dict with uptime information
        """
        result = self.executor.execute_sync("uptime")

        if not result.success:
            return {
                "success": False,
                "error": result.stderr,
            }

        return {
            "success": True,
            "uptime": result.stdout.strip(),
        }

    def get_os_info(self) -> Dict[str, Any]:
        """
        Get OS and distribution information.

        Returns:
            Dict with OS details
        """
        # Try /etc/os-release first (standard)
        result = self.executor.execute_sync("cat /etc/os-release")

        if not result.success:
            # Fallback to lsb_release
            result = self.executor.execute_sync("lsb_release -a")

        if not result.success:
            return {
                "success": False,
                "error": "Could not determine OS information",
            }

        return {
            "success": True,
            "output": result.stdout,
        }
