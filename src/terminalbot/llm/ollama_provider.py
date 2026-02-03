"""Ollama LLM provider for local models."""

import logging
from typing import Dict, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.

    Uses the ollama Python client for communication with local Ollama server.
    """

    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout: int = 10):
        """
        Initialize Ollama provider.

        Args:
            model: Model name (e.g., "llama3.2:1b")
            base_url: Ollama server URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._client = None

        logger.info(f"Initialized Ollama provider with model: {model}")

    def _get_client(self):
        """Lazy load Ollama client (only when needed)."""
        if self._client is None:
            try:
                import ollama

                self._client = ollama.Client(host=self.base_url, timeout=self.timeout)
                logger.info(f"Connected to Ollama at {self.base_url}")
            except ImportError:
                logger.error(
                    "ollama package not installed. Install with: pip install ollama"
                )
                raise ImportError(
                    "ollama package required for Ollama provider. "
                    "Install with: pip install terminalbot[ollama]"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Ollama client: {e}")
                raise

        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate completion using Ollama.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

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

            # Generate completion
            response = client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            return response["message"]["content"]

        except ImportError:
            raise
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}")

    def is_available(self) -> bool:
        """
        Check if Ollama is available.

        Returns:
            True if Ollama server is reachable and model exists
        """
        try:
            client = self._get_client()

            # Try to list models to check connectivity
            models = client.list()

            # Check if our model is available
            model_names = [m["name"] for m in models.get("models", [])]
            if self.model not in model_names:
                logger.warning(
                    f"Model {self.model} not found. Available models: {model_names}"
                )
                logger.info(f"Pulling model {self.model}...")
                # Try to pull the model
                client.pull(self.model)

            return True

        except ImportError:
            logger.debug("ollama package not installed")
            return False
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def get_name(self) -> str:
        """Get provider name."""
        return "ollama"

    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
        }
