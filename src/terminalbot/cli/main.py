"""Main CLI interface using Typer."""

import logging
import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from ..agent.coordinator import AgentCoordinator
from ..agent.safety import SafetyValidator
from ..config import get_config_path, get_settings
from ..executor import CommandExecutor
from ..plugins import ProcessesPlugin, SystemPlugin
from .output import (
    confirm_action,
    print_banner,
    print_capabilities,
    print_command,
    print_command_output,
    print_error,
    print_info,
    print_response,
    print_success,
    print_suggestions,
    print_warning,
    show_spinner,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="terminalbot",
    help="AI-powered Linux troubleshooting assistant",
    add_completion=True,
)


def process_query(query: str, lite: bool = False, force_llm: bool = False, dry_run: bool = False):
    """
    Process a user query.

    Args:
        query: Natural language query
        lite: Use lite mode (no LLM)
        force_llm: Force LLM usage
        dry_run: Don't execute commands
    """
    try:
        # Load settings
        settings = get_settings()

        # Override lite mode if flag is set
        if lite:
            settings.llm.enable_lite_mode = True

        # Initialize components
        executor = CommandExecutor(settings)
        safety = SafetyValidator(settings)

        # Initialize plugins
        plugins = [
            SystemPlugin(executor),
            ProcessesPlugin(executor, safety),
        ]

        # Initialize coordinator
        coordinator = AgentCoordinator(plugins, settings=settings)

        # Process query
        with show_spinner("Analyzing query..."):
            result = coordinator.process_query(query, force_llm=force_llm)

        # Handle result based on mode
        if not result["success"]:
            print_error(result.get("error", "Unknown error"))
            if "suggestions" in result and result["suggestions"]:
                print_suggestions(result["suggestions"])
            return

        # Rule-based mode - execute command
        if result["mode"] == "rule-based":
            command = result["command"]

            # Safety check
            requires_confirm, reason = safety.requires_confirmation(command)

            if requires_confirm:
                print_warning(reason or "This command requires confirmation")
                print_command(command)

                if not confirm_action("Execute this command?", default=False):
                    print_info("Command execution cancelled")
                    return

            # Execute command
            print_command(command)

            if dry_run:
                print_info("[DRY RUN] Command would be executed")
                return

            with show_spinner("Executing command..."):
                cmd_result = executor.execute_sync(command)

            # Show output
            if cmd_result.success:
                print_command_output(cmd_result.stdout)
                if cmd_result.stderr:
                    print_warning("Errors/Warnings:")
                    print_command_output(cmd_result.stderr)
            else:
                print_error("Command failed")
                print_command_output(cmd_result.stderr)

            # Analyze results with LLM if available
            if coordinator.llm_provider and not lite:
                with show_spinner("Analyzing results..."):
                    analysis = coordinator.analyze_results(query, cmd_result.output)
                if analysis != cmd_result.output:  # Only show if LLM provided analysis
                    print_response(analysis)

        # LLM mode - show response
        elif result["mode"] == "llm":
            print_response(result["response"])

    except KeyboardInterrupt:
        print_info("\nOperation cancelled by user")
        raise typer.Exit(code=0)
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        print_error(f"Failed to process query: {e}")
        raise typer.Exit(code=1)


@app.command(name="init")
def init():
    """Initialize TerminalBot configuration."""
    config_path = get_config_path()

    if config_path.exists():
        print_warning(f"Configuration already exists at: {config_path}")
        if not confirm_action("Overwrite existing configuration?"):
            print_info("Configuration unchanged")
            return

    try:
        # Load default settings
        settings = get_settings()

        # Save to config file
        settings.save_to_yaml(config_path)

        print_success(f"Configuration initialized at: {config_path}")
        print_info("\nNext steps:")
        print_info("1. Edit the config file to set your API keys (if using cloud LLM)")
        print_info("2. Or copy .env.example to .env and set environment variables")
        print_info("3. Try a query: terminalbot 'check system status'")

    except Exception as e:
        print_error(f"Failed to initialize configuration: {e}")
        raise typer.Exit(code=1)


# Config subcommand group
config_app = typer.Typer(name="config", help="Manage configuration settings")
app.add_typer(config_app)


@config_app.command(name="show")
def config_show():
    """Show current configuration."""
    try:
        config_path = get_config_path()
        if not config_path.exists():
            print_error("Configuration not initialized. Run: terminalbot init")
            return

        with open(config_path) as f:
            content = f.read()

        print_info(f"Configuration file: {config_path}\n")
        typer.echo(content)

    except Exception as e:
        print_error(f"Failed to show configuration: {e}")
        raise typer.Exit(code=1)


@config_app.command(name="set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key (e.g., llm.primary)")],
    value: Annotated[str, typer.Argument(help="Configuration value")],
):
    """Set a configuration value."""
    try:
        config_path = get_config_path()
        settings = get_settings()

        # Update setting
        settings.update_setting(key, value)

        # Save to file
        settings.save_to_yaml(config_path)

        print_success(f"Updated {key} = {value}")

    except Exception as e:
        print_error(f"Failed to update configuration: {e}")
        raise typer.Exit(code=1)


# Plugins subcommand group
plugins_app = typer.Typer(name="plugins", help="Manage plugins")
app.add_typer(plugins_app)


@plugins_app.command(name="list")
def plugins_list():
    """List available plugins."""
    try:
        # Initialize plugins
        executor = CommandExecutor()
        safety = SafetyValidator()

        available_plugins = [
            SystemPlugin(executor),
            ProcessesPlugin(executor, safety),
        ]

        print_info("Available plugins:\n")
        for plugin in available_plugins:
            typer.echo(f"  • {plugin.name}: {plugin.description}")
            typer.echo(f"    Tools: {len(plugin.get_tools())}")

    except Exception as e:
        print_error(f"Failed to list plugins: {e}")
        raise typer.Exit(code=1)


@app.command(name="capabilities")
def capabilities():
    """Show all available capabilities."""
    try:
        # Initialize components
        executor = CommandExecutor()
        safety = SafetyValidator()

        plugins = [
            SystemPlugin(executor),
            ProcessesPlugin(executor, safety),
        ]

        coordinator = AgentCoordinator(plugins)

        # Get and display capabilities
        caps = coordinator.list_capabilities()
        print_capabilities(caps)

    except Exception as e:
        print_error(f"Failed to show capabilities: {e}")
        raise typer.Exit(code=1)


def cli():
    """
    Entry point for the CLI.

    Handles routing between direct queries and subcommands.
    """
    # Check if first arg is a known subcommand
    known_commands = {"init", "config", "plugins", "capabilities"}

    # Get args (skip program name)
    args = sys.argv[1:]

    # If no args, show help
    if not args or args[0] in ["--help", "-h"]:
        app()
        return

    # Check if first non-option arg is a subcommand
    first_arg = None
    for arg in args:
        if not arg.startswith("-"):
            first_arg = arg
            break

    # If it's a known subcommand, let Typer handle it
    if first_arg in known_commands:
        app()
        return

    # Otherwise, treat everything as a query
    # Extract options
    lite = "--lite" in args
    force_llm = "--force-llm" in args
    dry_run = "--dry-run" in args
    verbose = "--verbose" in args or "-v" in args

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Remove options from args to get query text
    query_args = [
        arg for arg in args
        if arg not in ["--lite", "--force-llm", "--dry-run", "--verbose", "-v"]
    ]

    if not query_args:
        app()
        return

    query_text = " ".join(query_args)
    process_query(query_text, lite=lite, force_llm=force_llm, dry_run=dry_run)


if __name__ == "__main__":
    cli()
