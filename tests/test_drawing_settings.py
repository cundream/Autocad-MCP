"""Tests for the drawing_settings facade — friendly read/change of AutoCAD
system variables (units, precision, scales, osnap, …)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_read_snapshot_returns_known_keys(backend):
    snap = await backend.drawing_settings()
    assert snap["ok"] is True
    s = snap["settings"]
    for key in ("units", "linear_precision", "ltscale", "dimscale", "osmode"):
        assert key in s


async def test_set_and_read_back_units_by_name(backend):
    res = await backend.drawing_settings({"units": "mm"})
    assert res["ok"] is True
    assert res["applied"]["units"] == "mm"
    snap = await backend.drawing_settings()
    assert snap["settings"]["units"]["name"] == "mm"
    assert snap["settings"]["units"]["code"] == 4


async def test_set_units_cm_and_inch_codes(backend):
    await backend.drawing_settings({"units": "cm"})
    assert (await backend.drawing_settings())["settings"]["units"]["code"] == 5
    await backend.drawing_settings({"units": "inch"})
    assert (await backend.drawing_settings())["settings"]["units"]["code"] == 1


async def test_set_numeric_settings(backend):
    res = await backend.drawing_settings({
        "dimscale": 2.0, "linear_precision": 3, "ltscale": 0.5,
    })
    assert res["ok"] is True
    snap = (await backend.drawing_settings())["settings"]
    assert snap["dimscale"] == 2.0
    assert snap["linear_precision"] == 3
    assert snap["ltscale"] == 0.5


async def test_unknown_key_reports_error_without_failing_others(backend):
    res = await backend.drawing_settings({"dimscale": 1.5, "bogus_key": 1})
    assert res["applied"]["dimscale"] == 1.5
    assert "bogus_key" in res["errors"]
    assert res["ok"] is False


async def test_bad_unit_value_is_reported(backend):
    res = await backend.drawing_settings({"units": "furlongs"})
    assert "units" in res["errors"]


# ── server tool wiring ──────────────────────────────────────────────────────

class _FakeCtx:
    def __init__(self, backend):
        self.lifespan_context = {"backend": backend}

    async def info(self, *a, **k):
        pass


async def test_server_tool_reads_and_writes(backend):
    import server

    ctx = _FakeCtx(backend)
    write = await server.drawing_settings(settings={"units": "mm", "dimscale": 1.0}, ctx=ctx)
    assert write["ok"] is True
    read = await server.drawing_settings(ctx=ctx)
    assert read["settings"]["units"]["name"] == "mm"
