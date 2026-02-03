"""Rich output formatting for terminal."""

import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()
logger = logging.getLogger(__name__)


def print_banner():
    """Print TerminalBot banner."""
    console.print(
        "[bold blue]╔══════════════════════════════════════╗[/bold blue]"
    )
    console.print(
        "[bold blue]║[/bold blue]  [bold white]🤖 TerminalBot[/bold white] [dim]- AI Troubleshooting[/dim]  [bold blue]║[/bold blue]"
    )
    console.print(
        "[bold blue]╚══════════════════════════════════════╝[/bold blue]"
    )
    console.print()


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_command(command: str):
    """Print command being executed."""
    console.print(f"\n[dim]$[/dim] [bold cyan]{command}[/bold cyan]")


def print_command_output(output: str, truncate: bool = True, max_lines: int = 50):
    """
    Print command output with syntax highlighting.

    Args:
        output: Command output
        truncate: Whether to truncate long output
        max_lines: Maximum lines to show if truncating
    """
    if not output.strip():
        console.print("[dim]<no output>[/dim]")
        return

    lines = output.split("\n")

    if truncate and len(lines) > max_lines:
        # Show first portion and last portion
        shown_lines = lines[:max_lines // 2] + ["...", f"({len(lines) - max_lines} lines hidden)", "..."] + lines[-max_lines // 2:]
        output = "\n".join(shown_lines)

    console.print(Panel(output, border_style="dim", padding=(0, 1)))


def print_response(response: str):
    """Print LLM or bot response."""
    console.print(Panel(
        response,
        title="[bold blue]Response[/bold blue]",
        border_style="blue",
        padding=(1, 2),
    ))


def print_process_table(processes: List[Dict[str, Any]]):
    """
    Print process information as a table.

    Args:
        processes: List of process dicts
    """
    if not processes:
        console.print("[dim]No processes found[/dim]")
        return

    table = Table(title="Processes", show_header=True, header_style="bold cyan")
    table.add_column("PID", style="yellow", justify="right")
    table.add_column("Name", style="green")
    table.add_column("CPU %", justify="right")
    table.add_column("Memory %", justify="right")
    table.add_column("Command", style="dim")

    for proc in processes:
        table.add_row(
            str(proc.get("pid", "?")),
            proc.get("name", "?"),
            f"{proc.get('cpu_percent', 0):.1f}",
            f"{proc.get('memory_percent', 0):.1f}",
            proc.get("cmdline", "")[:60],  # Truncate command line
        )

    console.print(table)


def print_suggestions(suggestions: List[str]):
    """
    Print query suggestions.

    Args:
        suggestions: List of suggested queries
    """
    if not suggestions:
        return

    console.print("\n[bold]Did you mean:[/bold]")
    for i, suggestion in enumerate(suggestions, 1):
        console.print(f"  {i}. {suggestion}")


def print_capabilities(capabilities: List[str]):
    """
    Print available capabilities.

    Args:
        capabilities: List of capability descriptions
    """
    console.print("\n[bold cyan]Available Capabilities:[/bold cyan]\n")
    for cap in capabilities:
        console.print(cap)


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if user confirmed
    """
    default_str = "Y/n" if default else "y/N"
    response = console.input(f"[bold yellow]?[/bold yellow] {message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


def show_spinner(message: str = "Processing..."):
    """
    Show a spinner with message.

    Returns:
        Context manager for spinner
    """
    from rich.spinner import Spinner
    from rich.live import Live

    spinner = Spinner("dots", text=message)
    return Live(spinner, console=console, transient=True)
