"""Tool-profile (TOOL_PROFILE=lean/core/full) behavior."""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastmcp import Client

import config
import server

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def _restore_full_profile():
    """Profiles mutate global server enablement; always restore full."""
    yield
    await server._apply_tool_profile("full")


async def _registered_names() -> set[str]:
    return {tool.name for tool in await server._registered_tools() if getattr(tool, "name", None)}


async def test_lean_names_all_exist_in_registry():
    registered = await _registered_names()
    missing = server.LEAN_TOOL_NAMES - registered
    assert not missing, f"LEAN_TOOL_NAMES references unknown tools: {sorted(missing)}"


async def test_core_exclusions_all_exist_in_registry():
    registered = await _registered_names()
    missing = server.CORE_EXCLUDED_TOOL_NAMES - registered
    assert not missing, f"CORE_EXCLUDED_TOOL_NAMES references unknown tools: {sorted(missing)}"


async def test_full_profile_hides_only_gated_solids():
    """Full hides nothing except the opt-in 3D tools while ENABLE_3D=false."""
    info = await server._apply_tool_profile("full")
    assert info["profile"] == "full"
    assert set(info["disabled_tools"]) == set(server.SOLID_TOOL_NAMES)
    assert info["enabled_count"] == info["registered_count"] - len(server.SOLID_TOOL_NAMES)


async def test_invalid_profile_falls_back_to_full():
    info = await server._apply_tool_profile("does-not-exist")
    assert info["profile"] == "full"
    assert set(info["disabled_tools"]) == set(server.SOLID_TOOL_NAMES)


async def test_lean_profile_filters_client_view(monkeypatch):
    monkeypatch.setattr(config.settings, "backend", "ezdxf")
    monkeypatch.setattr(config.settings, "tool_profile", "lean")
    async with Client(server.mcp) as client:
        visible = {tool.name for tool in await client.list_tools()}
    assert visible == set(server.LEAN_TOOL_NAMES)


async def test_core_profile_hides_escape_hatches_keeps_engineering(monkeypatch):
    monkeypatch.setattr(config.settings, "backend", "ezdxf")
    monkeypatch.setattr(config.settings, "tool_profile", "core")
    async with Client(server.mcp) as client:
        visible = {tool.name for tool in await client.list_tools()}
    assert "system_run_command" not in visible
    assert "system_run_lisp" not in visible
    assert "gear_draw_spur_front_view" in visible
    assert "drawing_refine" in visible
    registered = await _registered_names()
    assert visible == registered - server.CORE_EXCLUDED_TOOL_NAMES - server.SOLID_TOOL_NAMES


async def test_profile_switch_is_idempotent():
    await server._apply_tool_profile("lean")
    info = await server._apply_tool_profile("full")
    assert set(info["disabled_tools"]) == set(server.SOLID_TOOL_NAMES)
    lean_again = await server._apply_tool_profile("lean")
    assert lean_again["enabled_count"] == len(server.LEAN_TOOL_NAMES)
