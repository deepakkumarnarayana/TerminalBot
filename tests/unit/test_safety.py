"""Tests for safety validator."""

import pytest

from terminalbot.agent.safety import SafetyValidator


def test_dangerous_command_detection():
    """Test detection of dangerous commands."""
    safety = SafetyValidator()

    assert safety.is_dangerous_command("rm -rf /")
    assert safety.is_dangerous_command("kill 1234")
    assert safety.is_dangerous_command("systemctl stop nginx")
    assert safety.is_dangerous_command("reboot")

    # Safe commands
    assert not safety.is_dangerous_command("ls -la")
    assert not safety.is_dangerous_command("ps aux")
    assert not safety.is_dangerous_command("systemctl status nginx")


def test_protected_process_detection():
    """Test detection of protected processes."""
    safety = SafetyValidator()

    # Protected by PID
    is_protected, reason = safety.is_protected_process("1")
    assert is_protected
    assert "PID 1" in reason

    # Protected by name
    is_protected, reason = safety.is_protected_process("systemd")
    assert is_protected
    assert "systemd" in reason.lower()

    is_protected, reason = safety.is_protected_process("sshd")
    assert is_protected

    # Not protected
    is_protected, reason = safety.is_protected_process("12345")
    assert not is_protected


def test_requires_confirmation():
    """Test confirmation requirement logic."""
    safety = SafetyValidator()

    # Should require confirmation
    requires, reason = safety.requires_confirmation("kill 1234")
    assert requires

    requires, reason = safety.requires_confirmation("rm file.txt")
    assert requires

    # Should not require confirmation
    requires, reason = safety.requires_confirmation("ls -la")
    assert not requires

    requires, reason = safety.requires_confirmation("echo 'hello'")
    assert not requires
