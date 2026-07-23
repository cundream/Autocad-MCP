"""Tests for drawing operations via ezdxf backend."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_drawing_info(backend):
    info = await backend.drawing_info()
    assert info.backend == "ezdxf"
    assert info.entity_count >= 0


async def test_drawing_new(backend):
    result = await backend.drawing_new()
    assert result.get("ok") is True


async def test_drawing_save_and_open(backend, tmp_path):
    await backend.entity_create_line(0, 0, 100, 0)
    save_path = str(tmp_path / "test_save.dxf")
    await backend.drawing_save(save_path)
    await backend.drawing_open(save_path)
    info = await backend.drawing_info()
    assert info.entity_count >= 1


async def test_drawing_export_dxf(backend, tmp_path):
    await backend.entity_create_circle(0, 0, 50)
    export_path = str(tmp_path / "export.dxf")
    result = await backend.drawing_export_dxf(export_path)
    assert result.get("ok") is True
    import os

    assert os.path.exists(export_path)


async def test_drawing_purge(backend):
    await backend.layer_create("TEMP_LAYER")
    result = await backend.drawing_purge()
    assert result.get("ok") is True


async def test_drawing_audit(backend):
    result = await backend.drawing_audit()
    assert result.get("ok") is True


async def test_drawing_undo(backend):
    await backend.entity_create_line(0, 0, 100, 0)
    result = await backend.drawing_undo()
    assert isinstance(result, dict)


async def test_drawing_redo(backend):
    result = await backend.drawing_redo()
    assert isinstance(result, dict)
