"""Reference v2 adapter for this repository."""

from __future__ import annotations

from pathlib import Path

from benchmarks.adapters.base import BenchmarkAdapter, TaskResult
from benchmarks.tasks_v2 import TaskSpec
from engineering.delivery import deliver_drawing
from engineering.layers import ensure_engineering_layers, ensure_standard_linetypes
from engineering.refiner import refine_drawing


class AutoCADMCPProAdapter(BenchmarkAdapter):
    name = "autocad-mcp-pro"

    def __init__(self, *, backend: str = "ezdxf"):
        self.backend_name = backend
        self.backend = None
        self.artifact_dir = Path()

    async def setup(self, artifact_dir: Path) -> None:
        if self.backend_name == "ezdxf":
            from backends.ezdxf_backend import EzdxfBackend

            self.backend = EzdxfBackend()
        elif self.backend_name == "com":
            from backends.com_backend import ComBackend

            self.backend = ComBackend()
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
        self.artifact_dir = artifact_dir
        await self.backend.connect()

    async def cleanup(self) -> None:
        if self.backend is not None:
            await self.backend.disconnect()

    def metadata(self) -> dict:
        return {
            "backend": self.backend_name,
            "capabilities": self.backend.capabilities().to_dict() if self.backend else None,
        }

    async def _reset(self) -> None:
        await self.backend.drawing_new()

    async def run_task(self, task: TaskSpec) -> TaskResult:
        await self._reset()
        handler = getattr(self, f"_task_{task.task_id}", None)
        if handler is None:
            return TaskResult(task.task_id, "unsupported", 0.0, "No adapter implementation")
        passed, metrics, artifacts = await handler()
        return TaskResult(
            task.task_id,
            "pass" if passed else "fail",
            100.0 if passed else 0.0,
            metrics=metrics,
            artifacts=artifacts,
        )

    async def _task_core_geometry(self):
        line = await self.backend.entity_create_line(0, 0, 3, 4)
        circle = await self.backend.entity_create_circle(10, 10, 2)
        info = await self.backend.entity_get(line.handle)
        passed = abs(float(info.properties["length"]) - 5.0) < 1e-6
        return passed and bool(circle.handle), {"line_length": info.properties["length"]}, []

    async def _task_modify_query(self):
        line = await self.backend.entity_create_line(0, 0, 10, 0)
        await self.backend.entity_move(line.handle, 5, 2)
        moved = await self.backend.entity_get(line.handle)
        return moved.properties["start"][:2] == [5.0, 2.0], {}, []

    async def _task_layers_linetypes(self):
        await ensure_standard_linetypes(self.backend)
        await ensure_engineering_layers(self.backend)
        layers = {item.name for item in await self.backend.layer_list()}
        linetypes = {item.upper() for item in await self.backend.linetype_list()}
        return "GEOMETRY" in layers and "CENTER" in linetypes, {}, []

    async def _task_dimensions(self):
        await ensure_engineering_layers(self.backend)
        dimension = await self.backend.dimension_linear(0, 0, 50, 0, 25, 10, layer="DIM")
        return "DIM" in dimension.type.upper(), {"entity_type": dimension.type}, []

    async def _task_table_mleader(self):
        await ensure_engineering_layers(self.backend)
        table = await self.backend.entity_create_table(
            0, 20, [["A", "1"]], headers=["ITEM", "QTY"], layer="TEXT"
        )
        leader = await self.backend.leader_create_mleader([[0, 0], [10, 10]], "NOTE", layer="DIM")
        representations = [
            table.properties.get("representation"),
            leader.properties.get("representation"),
        ]
        return all(representations), {"representations": representations}, []

    async def _task_transactions(self):
        await self.backend.transaction_begin()
        await self.backend.entity_create_circle(0, 0, 1)
        await self.backend.transaction_rollback()
        entities = await self.backend.entity_list(limit=100)
        return len(entities) == 0, {"entity_count": len(entities)}, []

    async def _task_preflight(self):
        result = await self.backend.drawing_preflight(
            "Benchmark plate",
            {
                "units": "mm",
                "part_type": "plate",
                "dimensions": {"width": 50, "height": 25},
                "tolerance_policy": "ISO 2768-m",
            },
        )
        return result.ready and result.spec_hash.startswith("sha256:"), {}, []

    async def _task_quality_refiner(self):
        await ensure_engineering_layers(self.backend)
        await self.backend.entity_create_line(0, 0, 10, 0, layer="GEOMETRY")
        await self.backend.entity_create_line(0, 0, 10, 0, layer="GEOMETRY")
        result = await refine_drawing(self.backend, focus=["duplicate_entities"])
        return result.final_score > result.initial_score, result.to_dict(), []

    async def _task_dxf_roundtrip(self):
        await self.backend.entity_create_line(0, 0, 10, 10)
        path = self.artifact_dir / "roundtrip.dxf"
        await self.backend.drawing_export_dxf(str(path))
        from backends.ezdxf_backend import EzdxfBackend

        reopened = EzdxfBackend()
        await reopened.connect()
        try:
            await reopened.drawing_open(str(path))
            count = (await reopened.drawing_info()).entity_count
        finally:
            await reopened.disconnect()
        return count == 1, {"entity_count": count}, [str(path)]

    async def _task_auditable_delivery(self):
        await ensure_engineering_layers(self.backend)
        await self.backend.entity_create_line(0, 0, 10, 0, layer="GEOMETRY")
        destination = self.artifact_dir / "delivery"
        result = await deliver_drawing(
            self.backend,
            destination,
            formats=["dxf"],
            min_score=0,
            strict_critique=False,
        )
        return result.status == "success", {"score": result.score}, [result.manifest_path]
