"""Tests for dimension creation via ezdxf backend."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_dimension_linear(backend):
    info = await backend.dimension_linear(0, 0, 100, 0, 50, 20, rotation=0)
    assert info.handle
    assert info.type == "DIMENSION"


@pytest.mark.xfail(reason="ezdxf API parameter mismatch in add_aligned_dim", strict=False)
async def test_dimension_aligned(backend):
    info = await backend.dimension_aligned(0, 0, 100, 50, 50, 60)
    assert info.handle
    assert info.type == "DIMENSION"


@pytest.mark.xfail(reason="ezdxf API parameter mismatch in add_angular_dim_2l", strict=False)
async def test_dimension_angular(backend):
    info = await backend.dimension_angular(0, 0, 100, 0, 0, 100, 50, 50)
    assert info.handle
    assert info.type == "DIMENSION"


async def test_dimension_radius(backend):
    await backend.entity_create_circle(50, 50, 30)
    info = await backend.dimension_radius(50, 50, 80, 50, leader_length=15)
    assert info.handle
    assert info.type == "DIMENSION"


async def test_dimension_diameter(backend):
    info = await backend.dimension_diameter(20, 50, 80, 50, leader_length=10)
    assert info.handle
    assert info.type == "DIMENSION"
