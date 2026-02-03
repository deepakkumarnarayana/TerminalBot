"""Rule-based command matching for lite mode (no LLM)."""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# Command pattern mappings (regex pattern -> command template)
COMMAND_PATTERNS = {
    # Process queries
    r"(?:is|check).*nginx.*(?:running|up|active)": "systemctl status nginx",
    r"(?:is|check).*apache.*(?:running|up|active)": "systemctl status httpd",
    r"(?:is|check).*(?:service|process)\s+(\w+).*(?:running|up|active)": "systemctl status {1}",
    r"(?:show|list|find).*process(?:es)?.*(\w+)": "ps aux | grep {1}",
    r"(?:show|list).*(?:all\s+)?process(?:es)?": "ps aux",
    r"top.*cpu": "ps aux --sort=-%cpu | head -n 11",
    r"top.*memory": "ps aux --sort=-%mem | head -n 11",
    r"top.*process(?:es)?": "top -bn1 | head -n 20",
    # System info
    r"(?:show|get|check).*system.*info": "uname -a && uptime",
    r"(?:show|check).*uptime": "uptime",
    r"(?:show|check).*kernel.*version": "uname -r",
    r"(?:show|check).*(?:os|distribution).*version": "cat /etc/os-release",
    # Disk and memory
    r"(?:show|check).*disk.*(?:space|usage)": "df -h",
    r"(?:show|check).*memory.*usage": "free -h",
    r"(?:show|check).*(?:ram|mem)": "free -h",
    # Network
    r"(?:show|check).*ip.*address": "ip addr show",
    r"(?:show|check).*network.*interfaces": "ip link show",
    r"(?:test|check).*internet.*connection": "ping -c 4 8.8.8.8",
    r"(?:test|check).*(?:connectivity|connection).*(?:to\s+)?(\S+)": "ping -c 4 {1}",
    # Services
    r"(?:show|list).*(?:running\s+)?services": "systemctl list-units --type=service --state=running",
    r"(?:show|list).*failed.*services": "systemctl list-units --type=service --state=failed",
    r"(?:show|check).*service.*(\w+)": "systemctl status {1}",
    # Logs
    r"(?:show|check|view).*system.*logs?": "journalctl -n 50 --no-pager",
    r"(?:show|check|view).*logs?.*(?:for\s+)?(\w+)": "journalctl -u {1} -n 50 --no-pager",
    # User and permissions
    r"(?:who|which).*(?:user|am i)": "whoami",
    r"(?:show|list).*logged.*users": "who",
    # File operations
    r"(?:list|show).*files.*(?:in\s+)?(\S+)": "ls -lah {1}",
    r"(?:list|show).*(?:current\s+)?(?:directory|dir|folder)": "ls -lah",
    r"(?:find|search).*file.*(\S+)": "find . -name '*{1}*' -type f",
    # General patterns
    r"what.*taking.*space": "du -sh * | sort -hr | head -n 10",
    r"(?:show|list).*environment.*variables": "env",
}


class RuleBasedMatcher:
    """
    Fast rule-based command matching without LLM.

    This provides instant responses for common queries with zero
    memory overhead (no model loading) and works offline.
    """

    def __init__(self):
        """Initialize matcher with compiled patterns."""
        # Compile patterns for better performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), command)
            for pattern, command in COMMAND_PATTERNS.items()
        ]
        logger.info(f"Initialized rule-based matcher with {len(self.compiled_patterns)} patterns")

    def match(self, query: str) -> Optional[Tuple[str, List[str]]]:
        """
        Match query against command patterns.

        Args:
            query: User query in natural language

        Returns:
            Tuple of (command, captured_groups) or None if no match
        """
        query = query.strip()

        for pattern, command_template in self.compiled_patterns:
            match = pattern.search(query)
            if match:
                # Extract captured groups for command template substitution
                groups = match.groups()

                # Substitute placeholders in command template
                if groups:
                    # Replace {1}, {2}, etc. with captured groups
                    command = command_template
                    for i, group in enumerate(groups, start=1):
                        if group:
                            command = command.replace(f"{{{i}}}", group)
                else:
                    command = command_template

                logger.info(f"Matched query to command: {command}")
                return command, list(groups) if groups else []

        logger.debug(f"No rule-based match found for: {query}")
        return None

    def get_suggestions(self, query: str, limit: int = 3) -> List[str]:
        """
        Get command suggestions based on partial query match.

        Args:
            query: Partial user query
            limit: Maximum number of suggestions

        Returns:
            List of suggested queries
        """
        query_lower = query.lower()
        suggestions = []

        # Extract keywords from query
        keywords = set(query_lower.split())

        for pattern, _ in self.compiled_patterns[:limit * 2]:  # Check more for better matches
            pattern_str = pattern.pattern.lower()

            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in pattern_str)

            if matches > 0:
                # Create a readable suggestion from the pattern
                suggestion = self._pattern_to_suggestion(pattern.pattern)
                if suggestion and suggestion not in suggestions:
                    suggestions.append(suggestion)

            if len(suggestions) >= limit:
                break

        return suggestions

    def _pattern_to_suggestion(self, pattern: str) -> str:
        """Convert regex pattern to readable suggestion."""
        # Remove regex syntax
        suggestion = pattern.replace(r"(?:", "").replace(")", "")
        suggestion = suggestion.replace(r"\s+", " ").replace(r"\w+", "<name>")
        suggestion = suggestion.replace(r"\S+", "<value>")
        suggestion = suggestion.replace(".*", " ")
        suggestion = suggestion.replace("|", " or ")

        # Clean up
        suggestion = re.sub(r"[?*+\[\]\\]", "", suggestion)
        suggestion = " ".join(suggestion.split())

        return suggestion if len(suggestion) < 100 else ""

    def list_capabilities(self) -> List[str]:
        """
        List all supported query patterns.

        Returns:
            List of capability descriptions
        """
        capabilities = []

        for pattern, command in COMMAND_PATTERNS.items():
            # Convert pattern to readable description
            desc = self._pattern_to_suggestion(pattern)
            if desc:
                capabilities.append(f"{desc} → {command}")

        return capabilities


# Singleton instance
_matcher: Optional[RuleBasedMatcher] = None


def get_matcher() -> RuleBasedMatcher:
    """Get or create rule-based matcher singleton."""
    global _matcher
    if _matcher is None:
        _matcher = RuleBasedMatcher()
    return _matcher
