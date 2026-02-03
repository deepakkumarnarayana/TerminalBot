"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers (Ollama, OpenAI, Anthropic) implement this interface.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system_prompt: System instruction (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and configured.

        Returns:
            True if provider can be used
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get provider name.

        Returns:
            Provider identifier (e.g., "ollama", "openai")
        """
        pass

    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the model being used.

        Returns:
            Dict with model details
        """
        return {
            "provider": self.get_name(),
            "model": "unknown",
        }
