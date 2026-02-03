"""Agent coordinator for orchestrating LLM and tools."""

import logging
import os
from typing import Dict, List, Optional

from ..llm import BaseLLMProvider, get_llm_provider
from ..plugins.base import BasePlugin
from .prompts import get_results_analysis_prompt, get_system_prompt
from .rule_based import get_matcher

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Coordinates LLM agent with available plugins and tools.

    This is a simplified coordinator that uses rule-based matching
    when possible, and falls back to LLM for complex queries.
    """

    def __init__(
        self,
        plugins: List[BasePlugin],
        llm_provider: Optional[BaseLLMProvider] = None,
        settings=None,
    ):
        """
        Initialize agent coordinator.

        Args:
            plugins: List of available plugins
            llm_provider: LLM provider (lazy loaded if None)
            settings: Settings instance
        """
        self.plugins = plugins
        self._llm_provider = llm_provider
        self.settings = settings
        self.matcher = get_matcher()  # Rule-based matcher

        logger.info(f"Initialized coordinator with {len(plugins)} plugins")

    @property
    def llm_provider(self) -> Optional[BaseLLMProvider]:
        """Lazy load LLM provider."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider(self.settings)
            if self._llm_provider:
                logger.info(f"Loaded LLM provider: {self._llm_provider.get_name()}")
            else:
                logger.info("No LLM provider available - using rule-based mode only")
        return self._llm_provider

    def process_query(self, query: str, force_llm: bool = False) -> Dict:
        """
        Process user query and generate response.

        Args:
            query: User's natural language query
            force_llm: Force LLM usage even if rule-based match exists

        Returns:
            Dict with response and metadata
        """
        # Get current working directory for context
        current_dir = os.getcwd()

        # Try rule-based matching first (unless forced to use LLM)
        if not force_llm:
            match_result = self.matcher.match(query)
            if match_result:
                command, groups = match_result
                logger.info(f"Rule-based match: {command}")

                return {
                    "success": True,
                    "mode": "rule-based",
                    "command": command,
                    "query": query,
                    "requires_execution": True,
                }

        # Fall back to LLM if available
        if self.llm_provider:
            logger.info("Using LLM to process query")
            return self._process_with_llm(query, current_dir)

        # No match and no LLM available
        logger.warning("No match found and no LLM available")
        return {
            "success": False,
            "mode": "none",
            "error": "Could not understand query. Try being more specific, or enable LLM support.",
            "suggestions": self.matcher.get_suggestions(query),
        }

    def _process_with_llm(self, query: str, current_dir: str) -> Dict:
        """
        Process query using LLM.

        Args:
            query: User query
            current_dir: Current working directory

        Returns:
            Dict with LLM response
        """
        try:
            # Generate system prompt with tool descriptions
            system_prompt = get_system_prompt(self.plugins, current_dir)

            # For now, we'll do simple LLM query without tool calling
            # (Full LangChain integration would be added in next iteration)
            response = self.llm_provider.generate(
                prompt=f"User query: {query}\n\nProvide helpful guidance for this query.",
                system_prompt=system_prompt,
            )

            return {
                "success": True,
                "mode": "llm",
                "response": response,
                "query": query,
                "provider": self.llm_provider.get_name(),
            }

        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return {
                "success": False,
                "mode": "llm",
                "error": f"LLM processing failed: {str(e)}",
            }

    def analyze_results(self, query: str, results: str) -> str:
        """
        Analyze command results using LLM.

        Args:
            query: Original query
            results: Command execution results

        Returns:
            Analysis and recommendations
        """
        if not self.llm_provider:
            return results  # Return raw results if no LLM

        try:
            prompt = get_results_analysis_prompt(query, results)
            analysis = self.llm_provider.generate(prompt)
            return analysis

        except Exception as e:
            logger.error(f"Result analysis failed: {e}")
            return results  # Fall back to raw results

    def list_capabilities(self) -> List[str]:
        """
        List all available capabilities.

        Returns:
            List of capability descriptions
        """
        capabilities = []

        # Add rule-based capabilities
        capabilities.append("**Rule-based capabilities:**")
        for cap in self.matcher.list_capabilities()[:10]:  # Show first 10
            capabilities.append(f"  - {cap}")

        # Add plugin capabilities
        capabilities.append("\n**Available plugins:**")
        for plugin in self.plugins:
            capabilities.append(f"  - {plugin.name}: {plugin.description}")

        # Add LLM status
        if self.llm_provider:
            info = self.llm_provider.get_model_info()
            capabilities.append(
                f"\n**LLM available:** {info['provider']} ({info.get('model', 'unknown')})"
            )
        else:
            capabilities.append("\n**LLM:** Not available (rule-based mode only)")

        return capabilities
