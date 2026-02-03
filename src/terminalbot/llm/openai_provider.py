"""OpenAI LLM provider."""

import logging
from typing import Dict, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider for GPT models.

    Uses the openai Python client for API access.
    """

    def __init__(
        self, api_key: str, model: str = "gpt-4o-mini", max_tokens: int = 2000, temperature: float = 0.1
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name
            max_tokens: Default max tokens
            temperature: Default temperature
        """
        self.api_key = api_key
        self.model = model
        self.default_max_tokens = max_tokens
        self.default_temperature = temperature
        self._client = None

        logger.info(f"Initialized OpenAI provider with model: {model}")

    def _get_client(self):
        """Lazy load OpenAI client (only when needed)."""
        if self._client is None:
            try:
                from openai import OpenAI

                if not self.api_key:
                    raise ValueError("OpenAI API key not configured")

                self._client = OpenAI(api_key=self.api_key)
                logger.info("Connected to OpenAI API")
            except ImportError:
                logger.error("openai package not installed. Install with: pip install openai")
                raise ImportError(
                    "openai package required for OpenAI provider. "
                    "Install with: pip install terminalbot[cloud]"
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
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
        Generate completion using OpenAI.

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

            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use defaults if not specified
            if temperature is None:
                temperature = self.default_temperature
            if max_tokens is None:
                max_tokens = self.default_max_tokens

            # Generate completion
            response = client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except ImportError:
            raise
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise RuntimeError(f"OpenAI generation failed: {e}")

    def is_available(self) -> bool:
        """
        Check if OpenAI is available.

        Returns:
            True if API key is configured
        """
        try:
            if not self.api_key:
                logger.debug("OpenAI API key not configured")
                return False

            # Client will be created on first use
            return True

        except ImportError:
            logger.debug("openai package not installed")
            return False
        except Exception as e:
            logger.debug(f"OpenAI not available: {e}")
            return False

    def get_name(self) -> str:
        """Get provider name."""
        return "openai"

    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        return {
            "provider": "openai",
            "model": self.model,
        }
