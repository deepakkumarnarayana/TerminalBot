"""Safe command execution with resource limits."""

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of command execution."""

    command: str
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    timed_out: bool = False
    truncated: bool = False
    working_directory: str = ""

    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.returncode == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Get combined output."""
        return self.stdout + self.stderr


class CommandExecutor:
    """
    Safe command executor with resource limits.

    Features:
    - Async execution with timeout
    - Output size limits
    - Working directory awareness
    - Command history logging
    """

    def __init__(self, settings=None):
        """Initialize executor with settings."""
        self.settings = settings or get_settings()
        self.history_file = Path(self.settings.logging.history_file).expanduser()
        self._ensure_history_file()

    def _ensure_history_file(self) -> None:
        """Create history file if it doesn't exist."""
        if self.settings.logging.log_commands:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                self.history_file.touch()

    def _log_command(self, command: str, result: CommandResult) -> None:
        """Log command to history file."""
        if not self.settings.logging.log_commands:
            return

        try:
            with open(self.history_file, "a") as f:
                timestamp = datetime.now().isoformat()
                status = "SUCCESS" if result.success else "FAILED"
                f.write(f"{timestamp} | {status} | {command}\n")
        except Exception as e:
            logger.warning(f"Failed to log command history: {e}")

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        dry_run: bool = False,
    ) -> CommandResult:
        """
        Execute a command asynchronously with resource limits.

        Args:
            command: Command to execute
            timeout: Timeout in seconds (uses config default if None)
            cwd: Working directory (uses current dir if None)
            dry_run: If True, only validate without executing

        Returns:
            CommandResult with execution details

        Raises:
            asyncio.TimeoutError: If command exceeds timeout
        """
        # Use config timeout if not specified
        if timeout is None:
            timeout = self.settings.execution.command_timeout

        # Determine working directory
        if cwd is None:
            cwd = self.settings.execution.working_directory or os.getcwd()

        logger.info(f"Executing command: {command} (cwd: {cwd})")

        # Dry run mode
        if dry_run:
            logger.info("DRY RUN - Command not executed")
            return CommandResult(
                command=command,
                returncode=0,
                stdout="[DRY RUN] Command would be executed",
                stderr="",
                execution_time=0.0,
                working_directory=cwd,
            )

        start_time = asyncio.get_event_loop().time()
        timed_out = False
        truncated = False

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                # Prevent command from spawning background processes
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Wait for completion with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Command timed out after {timeout}s: {command}")
                timed_out = True

                # Kill the process and its children
                try:
                    if os.name != "nt":
                        # Kill entire process group on Unix
                        os.killpg(os.getpgid(process.pid), 9)
                    else:
                        process.kill()
                except ProcessLookupError:
                    pass  # Process already terminated

                # Get whatever output was captured
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    stdout_bytes = b""
                    stderr_bytes = b"Command timed out and was terminated"

            # Decode output with error handling
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # Enforce output size limit
            max_size = self.settings.execution.max_output_size
            total_output_size = len(stdout) + len(stderr)

            if total_output_size > max_size:
                logger.warning(f"Output truncated: {total_output_size} > {max_size} bytes")
                truncated = True

                # Truncate proportionally
                stdout_limit = int(max_size * len(stdout) / total_output_size)
                stderr_limit = max_size - stdout_limit

                stdout = stdout[:stdout_limit] + "\n[... OUTPUT TRUNCATED ...]"
                stderr = stderr[:stderr_limit] + "\n[... OUTPUT TRUNCATED ...]"

            execution_time = asyncio.get_event_loop().time() - start_time

            result = CommandResult(
                command=command,
                returncode=process.returncode or (124 if timed_out else 0),
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                timed_out=timed_out,
                truncated=truncated,
                working_directory=cwd,
            )

            # Log to history
            self._log_command(command, result)

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            execution_time = asyncio.get_event_loop().time() - start_time

            result = CommandResult(
                command=command,
                returncode=1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                execution_time=execution_time,
                working_directory=cwd,
            )

            self._log_command(command, result)
            return result

    def execute_sync(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        dry_run: bool = False,
    ) -> CommandResult:
        """
        Synchronous wrapper for execute().

        Use this when you can't use async/await.
        """
        return asyncio.run(self.execute(command, timeout, cwd, dry_run))
