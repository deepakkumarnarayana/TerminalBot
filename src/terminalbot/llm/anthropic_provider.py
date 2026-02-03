"""Anthropic Claude LLM provider."""

import logging
from typing import Dict, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider for Claude models.

    Uses the anthropic Python client for API access.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 2000,
        temperature: float = 0.1,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name
            max_tokens: Default max tokens
            temperature: Default temperature
        """
        self.api_key = api_key
        self.model = model
        self.default_max_tokens = max_tokens
        self.default_temperature = temperature
        self._client = None

        logger.info(f"Initialized Anthropic provider with model: {model}")

    def _get_client(self):
        """Lazy load Anthropic client (only when needed)."""
        if self._client is None:
            try:
                from anthropic import Anthropic

                if not self.api_key:
                    raise ValueError("Anthropic API key not configured")

                self._client = Anthropic(api_key=self.api_key)
                logger.info("Connected to Anthropic API")
            except ImportError:
                logger.error(
                    "anthropic package not installed. Install with: pip install anthropic"
                )
                raise ImportError(
                    "anthropic package required for Anthropic provider. "
                    "Install with: pip install terminalbot[cloud]"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                raise

        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion using Anthropic Claude.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature (uses default if None)
            max_tokens: Maximum tokens (uses default if None)

        Returns:
            Generated text
        """
        try:
            client = self._get_client()

            # Use defaults if not specified
            if temperature is None:
                temperature = self.default_temperature
            if max_tokens is None:
                max_tokens = self.default_max_tokens

            # Build message
            messages = [{"role": "user", "content": prompt}]

            # Generate completion
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add system prompt if provided
            if system_prompt:
                kwargs["system"] = system_prompt

            response = client.messages.create(**kwargs)

            return response.content[0].text

        except ImportError:
            raise
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise RuntimeError(f"Anthropic generation failed: {e}")

    def is_available(self) -> bool:
        """
        Check if Anthropic is available.

        Returns:
            True if API key is configured
        """
        try:
            if not self.api_key:
                logger.debug("Anthropic API key not configured")
                return False

            # Client will be created on first use
            return True

        except ImportError:
            logger.debug("anthropic package not installed")
            return False
        except Exception as e:
            logger.debug(f"Anthropic not available: {e}")
            return False

    def get_name(self) -> str:
        """Get provider name."""
        return "anthropic"

    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        return {
            "provider": "anthropic",
            "model": self.model,
        }
