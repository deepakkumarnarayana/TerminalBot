"""TerminalBot - AI-powered Linux troubleshooting assistant."""

__version__ = "0.1.0"
__author__ = "TerminalBot Contributors"

from .config import get_settings
from .executor import CommandExecutor

__all__ = ["__version__", "get_settings", "CommandExecutor"]
