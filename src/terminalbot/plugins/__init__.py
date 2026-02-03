"""Plugin system for extending TerminalBot capabilities."""

from .base import BasePlugin
from .processes import ProcessesPlugin
from .system import SystemPlugin

__all__ = ["BasePlugin", "SystemPlugin", "ProcessesPlugin"]
