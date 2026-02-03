"""Tests for command executor."""

import pytest


@pytest.mark.asyncio
async def test_execute_simple_command(executor):
    """Test executing a simple command."""
    result = await executor.execute("echo 'hello world'")

    assert result.success
    assert "hello world" in result.stdout
    assert result.returncode == 0


@pytest.mark.asyncio
async def test_execute_with_timeout(executor):
    """Test command timeout enforcement."""
    result = await executor.execute("sleep 5", timeout=1)

    assert result.timed_out
    assert not result.success


@pytest.mark.asyncio
async def test_execute_failed_command(executor):
    """Test handling of failed commands."""
    result = await executor.execute("false")

    assert not result.success
    assert result.returncode != 0


@pytest.mark.asyncio
async def test_execute_with_working_directory(executor, tmp_path):
    """Test command execution in specific directory."""
    result = await executor.execute("pwd", cwd=str(tmp_path))

    assert result.success
    assert str(tmp_path) in result.stdout


def test_execute_sync(executor):
    """Test synchronous execution wrapper."""
    result = executor.execute_sync("echo 'test'")

    assert result.success
    assert "test" in result.stdout
