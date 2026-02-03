"""Tests for rule-based matcher."""

import pytest

from terminalbot.agent.rule_based import get_matcher


def test_matcher_process_queries():
    """Test matching process-related queries."""
    matcher = get_matcher()

    # Test various phrasings
    result = matcher.match("is nginx running?")
    assert result is not None
    command, groups = result
    assert "systemctl status nginx" in command

    result = matcher.match("check if apache is running")
    assert result is not None
    command, groups = result
    assert "systemctl status httpd" in command


def test_matcher_system_queries():
    """Test matching system info queries."""
    matcher = get_matcher()

    result = matcher.match("show disk space")
    assert result is not None
    command, groups = result
    assert "df -h" in command

    result = matcher.match("check memory usage")
    assert result is not None
    command, groups = result
    assert "free -h" in command


def test_matcher_top_processes():
    """Test matching top process queries."""
    matcher = get_matcher()

    result = matcher.match("top cpu processes")
    assert result is not None
    command, groups = result
    assert "ps aux" in command
    assert "cpu" in command.lower()


def test_matcher_no_match():
    """Test queries that don't match any pattern."""
    matcher = get_matcher()

    result = matcher.match("something completely random xyz123")
    assert result is None


def test_matcher_with_parameters():
    """Test matching queries with captured parameters."""
    matcher = get_matcher()

    result = matcher.match("find process named python")
    assert result is not None
    command, groups = result
    assert "python" in command or len(groups) > 0
