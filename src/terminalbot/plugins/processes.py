"""Process management plugin."""

import logging
import re
from typing import Any, Dict, List, Optional

import psutil

from ..agent.safety import SafetyValidator
from ..executor import CommandExecutor
from .base import BasePlugin

logger = logging.getLogger(__name__)


class ProcessesPlugin(BasePlugin):
    """
    Plugin for process management.

    Provides tools for finding processes, checking resource usage,
    and safely terminating processes.
    """

    def __init__(self, executor: CommandExecutor = None, safety: SafetyValidator = None):
        """
        Initialize processes plugin.

        Args:
            executor: Command executor (creates one if None)
            safety: Safety validator (creates one if None)
        """
        self.executor = executor or CommandExecutor()
        self.safety = safety or SafetyValidator()

    @property
    def name(self) -> str:
        """Plugin name."""
        return "processes"

    @property
    def description(self) -> str:
        """Plugin description."""
        return "Process management (find, list, monitor, terminate processes)"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of process management tools."""
        return [
            {
                "name": "find_process",
                "description": "Find processes by name or pattern",
                "function": self.find_process,
                "parameters": {
                    "name": {
                        "type": "string",
                        "description": "Process name or pattern to search for",
                        "required": True,
                    }
                },
            },
            {
                "name": "list_top_processes",
                "description": "List top processes by CPU or memory usage",
                "function": self.list_top_processes,
                "parameters": {
                    "sort_by": {
                        "type": "string",
                        "description": "Sort by 'cpu' or 'memory' (default: cpu)",
                        "required": False,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of processes to return (default: 10)",
                        "required": False,
                    },
                },
            },
            {
                "name": "get_process_details",
                "description": "Get detailed information about a specific process",
                "function": self.get_process_details,
                "parameters": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID",
                        "required": True,
                    }
                },
            },
            {
                "name": "check_if_running",
                "description": "Check if a process is currently running",
                "function": self.check_if_running,
                "parameters": {
                    "name": {
                        "type": "string",
                        "description": "Process name to check",
                        "required": True,
                    }
                },
            },
        ]

    def find_process(self, name: str) -> Dict[str, Any]:
        """
        Find processes matching a name pattern.

        Args:
            name: Process name or pattern

        Returns:
            Dict with matching processes
        """
        try:
            processes = []
            name_lower = name.lower()

            for proc in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_percent"]):
                try:
                    proc_info = proc.info
                    if name_lower in proc_info["name"].lower():
                        processes.append(
                            {
                                "pid": proc_info["pid"],
                                "name": proc_info["name"],
                                "cmdline": " ".join(proc_info["cmdline"] or []),
                                "cpu_percent": proc_info.get("cpu_percent", 0),
                                "memory_percent": proc_info.get("memory_percent", 0),
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return {
                "success": True,
                "count": len(processes),
                "processes": processes,
            }

        except Exception as e:
            logger.error(f"Failed to find process: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def list_top_processes(self, sort_by: str = "cpu", limit: int = 10) -> Dict[str, Any]:
        """
        List top processes by resource usage.

        Args:
            sort_by: Sort by 'cpu' or 'memory'
            limit: Number of processes to return

        Returns:
            Dict with top processes
        """
        try:
            processes = []

            # Collect process info
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    proc.cpu_percent()  # First call returns 0, so we call twice
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Small delay for accurate CPU measurement
            import time
            time.sleep(0.1)

            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "cmdline"]):
                try:
                    proc_info = proc.info
                    processes.append(
                        {
                            "pid": proc_info["pid"],
                            "name": proc_info["name"],
                            "cmdline": " ".join(proc_info["cmdline"] or [])[:100],  # Truncate
                            "cpu_percent": proc_info.get("cpu_percent", 0) or 0,
                            "memory_percent": proc_info.get("memory_percent", 0) or 0,
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort processes
            if sort_by == "memory":
                processes.sort(key=lambda p: p["memory_percent"], reverse=True)
            else:  # default to CPU
                processes.sort(key=lambda p: p["cpu_percent"], reverse=True)

            # Limit results
            top_processes = processes[:limit]

            return {
                "success": True,
                "sort_by": sort_by,
                "count": len(top_processes),
                "processes": top_processes,
            }

        except Exception as e:
            logger.error(f"Failed to list processes: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        """
        Get detailed information about a process.

        Args:
            pid: Process ID

        Returns:
            Dict with process details
        """
        try:
            proc = psutil.Process(pid)
            info = proc.as_dict(
                attrs=[
                    "pid",
                    "name",
                    "cmdline",
                    "cpu_percent",
                    "memory_percent",
                    "status",
                    "create_time",
                    "username",
                ]
            )

            return {
                "success": True,
                "process": info,
            }

        except psutil.NoSuchProcess:
            return {
                "success": False,
                "error": f"Process {pid} not found",
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "error": f"Access denied to process {pid}",
            }
        except Exception as e:
            logger.error(f"Failed to get process details: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def check_if_running(self, name: str) -> Dict[str, Any]:
        """
        Check if a process is running.

        Args:
            name: Process name

        Returns:
            Dict with running status
        """
        result = self.find_process(name)

        if not result["success"]:
            return result

        is_running = result["count"] > 0

        return {
            "success": True,
            "running": is_running,
            "count": result["count"],
            "processes": result["processes"] if is_running else [],
        }
