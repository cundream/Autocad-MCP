from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backends.base import EntityInfo
from backends.com_backend import ComBackend

pytestmark = pytest.mark.asyncio


async def test_ezdxf_table_returns_composite_contract(backend):
    result = await backend.entity_create_table(
        10,
        100,
        rows=[["P-01", "4"], ["P-02", "2"]],
        headers=["Part", "Qty"],
        title="BOM",
        layer="TEXT",
    )

    assert result.type == "TABLE"
    assert result.layer == "TEXT"
    assert result.properties["representation"] == "composite"
    assert result.properties["logical_group_id"].startswith("table:")
    assert len(result.properties["child_handles"]) >= 10
    assert result.properties["bounds"] == {"min": [10.0, 72.0], "max": [30.0, 100.0]}


async def test_ezdxf_table_survives_save_and_reopen(backend, tmp_path):
    result = await backend.entity_create_table(0, 30, rows=[["A", "1"]], headers=["Name", "Qty"])
    path = tmp_path / "table.dxf"
    await backend.drawing_save_as(str(path), fmt="dxf")
    await backend.drawing_open(str(path))

    entities = await backend.entity_list(limit=100)
    handles = {entity.handle for entity in entities}
    texts = {
        entity.properties.get("text") for entity in entities if entity.type in {"TEXT", "MTEXT"}
    }
    assert set(result.properties["child_handles"]).issubset(handles)
    assert {"Name", "Qty", "A", "1"}.issubset(texts)


async def test_table_rejects_ragged_rows_and_size_limit(backend):
    with pytest.raises(RuntimeError, match="same number of columns"):
        await backend.entity_create_table(0, 0, rows=[["A", "B"], ["C"]])

    with pytest.raises(RuntimeError, match="200 rows"):
        await backend.entity_create_table(0, 0, rows=[["A"]] * 201)


async def test_ezdxf_mleader_returns_composite_contract(backend):
    result = await backend.leader_create_mleader(
        [[0, 0], [10, 5], [30, 5]],
        "SURFACE A",
        layer="DIM",
    )

    assert result.type == "MLEADER"
    assert result.properties["representation"] == "composite"
    assert result.properties["logical_group_id"].startswith("mleader:")
    assert result.properties["text"] == "SURFACE A"
    assert len(result.properties["child_handles"]) == 3


async def test_mleader_requires_two_points(backend):
    with pytest.raises(RuntimeError, match="at least two points"):
        await backend.leader_create_mleader([[0, 0]], "note")


async def test_com_table_uses_native_add_table():
    backend = ComBackend()

    async def run_inline(func, *args, **kwargs):
        return func(*args, **kwargs)

    backend._run = run_inline
    mspace = MagicMock()
    table = MagicMock()
    table.Handle = "A1"
    mspace.AddTable.return_value = table
    info = EntityInfo("A1", "ACAD_TABLE", "TEXT", 256, "ByLayer", True, {})

    with (
        patch("backends.com_backend._msp", return_value=mspace),
        patch("backends.com_backend._apoint", side_effect=lambda *p: tuple(p)),
        patch("backends.com_backend._entity_info", return_value=info),
        patch("backends.com_backend._apply_entity_attrs"),
        patch("backends.com_backend._regen"),
    ):
        result = await backend.entity_create_table(
            0, 50, [["A", "1"]], headers=["Name", "Qty"], title="BOM"
        )

    mspace.AddTable.assert_called_once()
    assert mspace.AddTable.call_args[0][1:3] == (3, 2)
    assert table.SetText.call_count == 6
    assert result.type == "TABLE"
    assert result.properties["representation"] == "native"


async def test_com_mleader_uses_native_add_mleader():
    backend = ComBackend()

    async def run_inline(func, *args, **kwargs):
        return func(*args, **kwargs)

    backend._run = run_inline
    mspace = MagicMock()
    leader = MagicMock()
    leader.Handle = "B1"
    mspace.AddMLeader.return_value = leader
    info = EntityInfo("B1", "ACAD_MLEADER", "DIM", 256, "ByLayer", True, {})

    with (
        patch("backends.com_backend._msp", return_value=mspace),
        patch("backends.com_backend._av", side_effect=lambda values: values),
        patch("backends.com_backend._entity_info", return_value=info),
        patch("backends.com_backend._apply_entity_attrs"),
        patch("backends.com_backend._regen"),
    ):
        result = await backend.leader_create_mleader([[0, 0], [20, 5]], "NOTE")

    mspace.AddMLeader.assert_called_once_with([0.0, 0.0, 0.0, 20.0, 5.0, 0.0], 0)
    assert leader.TextString == "NOTE"
    assert result.type == "MLEADER"
    assert result.properties["representation"] == "native"


async def test_server_registers_table_and_mleader_tools():
    import server

    names = {tool.name for tool in await server._registered_tools()}
    assert "entity_create_table" in names
    assert "leader_create_mleader" in names
