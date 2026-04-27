"""Shared fixtures for AutoCAD MCP tests."""

import pytest_asyncio

from backends.ezdxf_backend import EzdxfBackend


@pytest_asyncio.fixture
async def backend():
    """Create an ezdxf backend with a fresh empty document."""
    b = EzdxfBackend()
    await b.connect()
    await b.drawing_new()
    yield b
    await b.disconnect()
