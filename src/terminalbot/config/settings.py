"""Configuration settings using Pydantic."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaConfig(BaseModel):
    """Ollama LLM configuration."""

    model: str = "llama3.2:1b"
    base_url: str = "http://localhost:11434"
    timeout: int = 10


class OpenAIConfig(BaseModel):
    """OpenAI LLM configuration."""

    model: str = "gpt-4o-mini"
    api_key: str = ""
    max_tokens: int = 2000
    temperature: float = 0.1

    @field_validator("api_key")
    @classmethod
    def resolve_env_vars(cls, v: str) -> str:
        """Resolve environment variable references."""
        if v.startswith("env:"):
            env_var = v[4:]
            return os.getenv(env_var, "")
        return v


class AnthropicConfig(BaseModel):
    """Anthropic Claude configuration."""

    model: str = "claude-3-5-haiku-20241022"
    api_key: str = ""
    max_tokens: int = 2000
    temperature: float = 0.1

    @field_validator("api_key")
    
    @classmethod
    def resolve_env_vars(cls, v: str) -> str:
        """Resolve environment variable references."""
        if v.startswith("env:"):
            env_var = v[4:]
            return os.getenv(env_var, "")
        return v


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    primary: Optional[str] = "ollama"
    fallback: Optional[str] = "openai"
    enable_lite_mode: bool = False
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)


class ExecutionConfig(BaseModel):
    """Command execution configuration."""

    command_timeout: int = 30
    max_output_size: int = 10485760  # 10MB
    max_concurrent_commands: int = 3
    working_directory: Optional[str] = None


class SafetyConfig(BaseModel):
    """Safety settings configuration."""

    require_confirmation: bool = True
    protected_processes: List[str] = Field(
        default_factory=lambda: ["systemd", "init", "sshd", "NetworkManager", "dbus-daemon"]
    )
    protected_pids: List[int] = Field(default_factory=lambda: [1])
    dangerous_commands: List[str] = Field(
        default_factory=lambda: [
            "rm",
            "kill",
            "killall",
            "pkill",
            "systemctl stop",
            "systemctl disable",
            "systemctl mask",
            "reboot",
            "shutdown",
            "poweroff",
        ]
    )


class OutputConfig(BaseModel):
    """Output formatting configuration."""

    use_rich: bool = True
    theme: str = "auto"
    show_timestamps: bool = True
    truncate_long_output: bool = True
    max_output_lines: int = 100


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    file: Optional[str] = None
    log_commands: bool = True
    history_file: str = "~/.terminalbot_history"


class PluginsConfig(BaseModel):
    """Plugin configuration."""

    autoload: bool = True
    additional_dirs: List[str] = Field(default_factory=list)
    disabled: List[str] = Field(default_factory=list)


class PerformanceConfig(BaseModel):
    """Performance tuning configuration."""

    cache_ttl: int = 3600  # 1 hour
    lazy_load_llm: bool = True
    async_execution: bool = True


class Settings(BaseSettings):
    """Main settings class with all configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TERMINALBOT_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    @classmethod
    def load_from_yaml(cls, config_path: Path) -> "Settings":
        """Load settings from YAML file."""
        if not config_path.exists():
            # Load defaults from package
            defaults_path = Path(__file__).parent / "defaults.yaml"
            if defaults_path.exists():
                with open(defaults_path) as f:
                    config_data = yaml.safe_load(f)
            else:
                config_data = {}
        else:
            with open(config_path) as f:
                config_data = yaml.safe_load(f) or {}

        return cls(**config_data)

    def save_to_yaml(self, config_path: Path) -> None:
        """Save settings to YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and dump to YAML
        config_dict = self.model_dump(mode="json")
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    def update_setting(self, key_path: str, value: Any) -> None:
        """Update a setting using dot notation (e.g., 'llm.primary')."""
        keys = key_path.split(".")
        obj = self

        # Navigate to the parent object
        for key in keys[:-1]:
            obj = getattr(obj, key)

        # Set the final value
        setattr(obj, keys[-1], value)


# Singleton instance
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[Path] = None, reload: bool = False) -> Settings:
    """
    Get settings singleton.

    Args:
        config_path: Path to config file (default: ~/.config/terminalbot/config.yaml)
        reload: Force reload from file

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None or reload:
        if config_path is None:
            # Default config location
            config_path = Path.home() / ".config" / "terminalbot" / "config.yaml"

        _settings = Settings.load_from_yaml(config_path)

    return _settings


def get_config_path() -> Path:
    """Get the default config file path."""
    return Path.home() / ".config" / "terminalbot" / "config.yaml"
