"""LLM provider factory with fallback support."""

import logging
from typing import Optional

from ..config import get_settings
from .anthropic_provider import AnthropicProvider
from .base import BaseLLMProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


def create_provider(provider_name: str, settings=None) -> Optional[BaseLLMProvider]:
    """
    Create an LLM provider instance.

    Args:
        provider_name: Provider name (ollama, openai, anthropic)
        settings: Settings instance (uses default if None)

    Returns:
        Provider instance or None if creation failed
    """
    if settings is None:
        settings = get_settings()

    try:
        if provider_name == "ollama":
            config = settings.llm.ollama
            provider = OllamaProvider(
                model=config.model, base_url=config.base_url, timeout=config.timeout
            )

        elif provider_name == "openai":
            config = settings.llm.openai
            if not config.api_key:
                logger.warning("OpenAI API key not configured")
                return None
            provider = OpenAIProvider(
                api_key=config.api_key,
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        elif provider_name == "anthropic":
            config = settings.llm.anthropic
            if not config.api_key:
                logger.warning("Anthropic API key not configured")
                return None
            provider = AnthropicProvider(
                api_key=config.api_key,
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        else:
            logger.error(f"Unknown provider: {provider_name}")
            return None

        # Verify provider is available
        if not provider.is_available():
            logger.warning(f"Provider {provider_name} is not available")
            return None

        logger.info(f"Successfully created {provider_name} provider")
        return provider

    except Exception as e:
        logger.warning(f"Failed to create {provider_name} provider: {e}")
        return None


def get_llm_provider(settings=None) -> Optional[BaseLLMProvider]:
    """
    Get LLM provider with fallback support.

    Tries primary provider first, then fallback if primary fails.

    Args:
        settings: Settings instance (uses default if None)

    Returns:
        Provider instance or None if all providers failed
    """
    if settings is None:
        settings = get_settings()

    # Check if lite mode is enabled (no LLM)
    if settings.llm.enable_lite_mode:
        logger.info("Lite mode enabled - LLM disabled")
        return None

    # Try primary provider
    if settings.llm.primary:
        logger.info(f"Trying primary provider: {settings.llm.primary}")
        provider = create_provider(settings.llm.primary, settings)
        if provider:
            return provider

    # Try fallback provider
    if settings.llm.fallback and settings.llm.fallback != settings.llm.primary:
        logger.info(f"Trying fallback provider: {settings.llm.fallback}")
        provider = create_provider(settings.llm.fallback, settings)
        if provider:
            return provider

    logger.warning("No LLM provider available - falling back to rule-based mode")
    return None


# Singleton instance (lazy loaded)
_provider: Optional[BaseLLMProvider] = None
_provider_initialized = False


def get_cached_provider(settings=None) -> Optional[BaseLLMProvider]:
    """
    Get cached LLM provider instance.

    This avoids recreating the provider on every query, which is
    expensive for providers that need to establish connections.

    Args:
        settings: Settings instance (uses default if None)

    Returns:
        Cached provider instance or None
    """
    global _provider, _provider_initialized

    if not _provider_initialized:
        _provider = get_llm_provider(settings)
        _provider_initialized = True

    return _provider


def reset_provider() -> None:
    """
    Reset cached provider (useful for testing or config changes).
    """
    global _provider, _provider_initialized
    _provider = None
    _provider_initialized = False
