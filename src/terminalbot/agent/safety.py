"""Safety validation for command execution."""

import logging
import re
from typing import Dict, Optional, Tuple

import psutil

from ..config import get_settings

logger = logging.getLogger(__name__)


class SafetyValidator:
    """
    Validates commands for safety before execution.

    Features:
    - Detects destructive commands
    - Protects critical processes and PIDs
    - Requires confirmation for dangerous operations
    """

    def __init__(self, settings=None):
        """Initialize safety validator with settings."""
        self.settings = settings or get_settings()

    def is_dangerous_command(self, command: str) -> bool:
        """
        Check if command is potentially dangerous.

        Args:
            command: Command to check

        Returns:
            True if command requires confirmation
        """
        command_lower = command.lower().strip()

        # Check against dangerous command list
        for dangerous_cmd in self.settings.safety.dangerous_commands:
            # Match command at word boundary (not substring)
            pattern = r"\b" + re.escape(dangerous_cmd) + r"\b"
            if re.search(pattern, command_lower):
                logger.warning(f"Dangerous command detected: {dangerous_cmd}")
                return True

        return False

    def is_protected_process(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if process is protected from termination.

        Args:
            identifier: Process name or PID

        Returns:
            Tuple of (is_protected, reason)
        """
        # Check if identifier is a PID
        try:
            pid = int(identifier)
            if pid in self.settings.safety.protected_pids:
                return True, f"PID {pid} is a protected system process"

            # Get process info to check name
            try:
                proc = psutil.Process(pid)
                process_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False, None

        except ValueError:
            # Identifier is a process name
            process_name = identifier

        # Check against protected process names
        process_name_lower = process_name.lower()
        for protected in self.settings.safety.protected_processes:
            if protected.lower() in process_name_lower:
                return True, f"'{protected}' is a protected system process"

        return False, None

    def validate_kill_command(self, command: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate a kill/killall/pkill command.

        Args:
            command: Command to validate

        Returns:
            Tuple of (is_safe, error_message, process_info)
        """
        # Extract PIDs or process names from command
        tokens = command.split()

        if not tokens:
            return False, "Empty command", None

        cmd = tokens[0]

        # Handle different kill variants
        if cmd in ["kill", "killall", "pkill"]:
            if len(tokens) < 2:
                return False, f"No target specified for {cmd}", None

            # Get target (PID or process name)
            target = tokens[-1]  # Usually last argument

            # Check if target is protected
            is_protected, reason = self.is_protected_process(target)

            if is_protected:
                return False, reason, None

            # Try to get process info for display
            process_info = self._get_process_info(target)

            return True, None, process_info

        # Handle systemctl stop/disable/mask
        elif "systemctl" in cmd:
            if len(tokens) < 3:
                return False, "Incomplete systemctl command", None

            action = tokens[1] if len(tokens) > 1 else ""
            service = tokens[2] if len(tokens) > 2 else ""

            if action in ["stop", "disable", "mask"]:
                # Check if service is protected
                service_name = service.replace(".service", "")
                is_protected, reason = self.is_protected_process(service_name)

                if is_protected:
                    return False, reason, None

                return True, None, {"service": service, "action": action}

        return True, None, None

    def _get_process_info(self, identifier: str) -> Optional[Dict]:
        """
        Get process information for display.

        Args:
            identifier: PID or process name

        Returns:
            Dict with process info or None
        """
        try:
            # Try as PID first
            try:
                pid = int(identifier)
                proc = psutil.Process(pid)
                return {
                    "pid": pid,
                    "name": proc.name(),
                    "cmdline": " ".join(proc.cmdline()),
                    "cpu_percent": proc.cpu_percent(),
                    "memory_percent": proc.memory_percent(),
                }
            except ValueError:
                # It's a process name
                processes = []
                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    if identifier.lower() in proc.info["name"].lower():
                        processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "cmdline": " ".join(proc.info["cmdline"] or []),
                            }
                        )

                if processes:
                    return {"matching_processes": processes, "count": len(processes)}

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not get process info: {e}")

        return None

    def requires_confirmation(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if command requires user confirmation.

        Args:
            command: Command to check

        Returns:
            Tuple of (requires_confirmation, reason)
        """
        if not self.settings.safety.require_confirmation:
            return False, None

        # Check if it's a dangerous command
        if self.is_dangerous_command(command):
            # Validate kill commands specifically
            if any(
                kill_cmd in command.lower()
                for kill_cmd in ["kill", "killall", "pkill", "systemctl stop"]
            ):
                is_safe, error, process_info = self.validate_kill_command(command)

                if not is_safe:
                    return True, error

                # Even if safe, still require confirmation
                reason = "This command will terminate processes"
                if process_info:
                    if "matching_processes" in process_info:
                        reason += f" ({process_info['count']} matching processes)"
                    elif "service" in process_info:
                        reason += f" (service: {process_info['service']})"

                return True, reason

            return True, "This is a potentially destructive command"

        return False, None
