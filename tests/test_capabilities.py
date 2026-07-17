from __future__ import annotations

from unittest.mock import patch

import pytest

from backends.base import CapabilityMap, FeatureCapability


def test_capability_types_serialize_stably():
    caps = CapabilityMap(
        backend="demo",
        features={"table": FeatureCapability(True, "native")},
    )

    assert caps.to_dict() == {
        "backend": "demo",
        "features": {
            "table": {"supported": True, "mode": "native", "reason": None},
        },
    }


@pytest.mark.asyncio
async def test_ezdxf_capabilities_are_machine_readable(backend):
    caps = backend.capabilities().to_dict()

    assert caps["backend"] == "ezdxf"
    assert caps["features"]["table"] == {
        "supported": True,
        "mode": "composite",
        "reason": None,
    }
    assert caps["features"]["mleader"]["mode"] == "composite"
    assert caps["features"]["paper_space"]["supported"] is False
    assert caps["features"]["solid_3d"]["supported"] is False


@pytest.mark.asyncio
async def test_ezdxf_render_capabilities_follow_optional_dependency(backend):
    with patch("backends.ezdxf_backend.find_spec", return_value=None):
        caps = backend.capabilities().to_dict()

    assert caps["features"]["pdf"] == {
        "supported": False,
        "mode": None,
        "reason": "optional_dependency_missing:matplotlib",
    }
    assert caps["features"]["png"]["supported"] is False


@pytest.mark.asyncio
async def test_system_capabilities_tool_uses_backend_map(backend):
    import server

    class Ctx:
        lifespan_context = {"backend": backend}

    result = await server.system_capabilities(ctx=Ctx())

    assert result == backend.capabilities().to_dict()


@pytest.mark.asyncio
async def test_system_about_uses_package_version_and_capability_summary(backend):
    import server

    class Ctx:
        lifespan_context = {"backend": backend}

    result = await server.system_about(ctx=Ctx())

    assert result["version"] == "1.3.0"
    assert result["capabilities"]["table"]["mode"] == "composite"
