"""Command line runner for the fixed-task benchmark v2 adapter contract."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.adapters.base import BenchmarkAdapter, TaskResult
from benchmarks.tasks_v2 import TASKS_V2, TaskSpec, task_by_id


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _hash_file(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path),
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def _normalize_artifacts(result: TaskResult) -> None:
    normalized: list[dict] = []
    for artifact in result.artifacts:
        if isinstance(artifact, dict):
            normalized.append(dict(artifact))
            continue
        path = Path(artifact).resolve()
        if path.is_file():
            normalized.append(_hash_file(path))
        else:
            normalized.append({"path": str(path), "missing": True})
    result.artifacts = normalized


async def run_tasks(
    adapter: BenchmarkAdapter,
    tasks: list[TaskSpec] | tuple[TaskSpec, ...],
    artifact_dir: str | Path,
    *,
    timeout: float = 30.0,
) -> dict:
    destination = Path(artifact_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    results: list[TaskResult] = []
    await adapter.setup(destination)
    try:
        for task in tasks:
            started = time.perf_counter()
            try:
                result = await asyncio.wait_for(adapter.run_task(task), timeout=timeout)
            except TimeoutError:
                result = TaskResult(task.task_id, "timeout", 0.0, f"Exceeded {timeout}s")
            except Exception as exc:
                result = TaskResult(task.task_id, "fail", 0.0, str(exc), stderr_summary=str(exc))
            result.duration_ms = round((time.perf_counter() - started) * 1000, 2)
            _normalize_artifacts(result)
            results.append(result)
    finally:
        await adapter.cleanup()

    attempted = len(results)
    passed = sum(item.status == "pass" for item in results)
    supported = [item for item in results if item.status != "unsupported"]
    weight_by_id = {task.task_id: task.weight for task in tasks}
    total_weight = sum(weight_by_id.values())
    supported_weight = sum(weight_by_id[item.task_id] for item in supported)
    weighted_score = sum(
        weight_by_id[item.task_id] * item.score
        for item in results
        if item.status != "unsupported"
    )
    return {
        "schema_version": "2.0",
        "adapter": adapter.name,
        "adapter_metadata": adapter.metadata(),
        "git_sha": _git_sha(),
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "timeout_seconds": timeout,
        "summary": {
            "attempted": attempted,
            "passed": passed,
            "supported": len(supported),
            "unsupported": sum(item.status == "unsupported" for item in results),
            "coverage_percent": (
                round(supported_weight / total_weight * 100, 2) if total_weight else 0.0
            ),
            "score": round(weighted_score / total_weight, 2) if total_weight else 0.0,
        },
        "results": [item.to_dict() for item in results],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List the fixed benchmark tasks")
    parser.add_argument("--server", default="autocad-mcp-pro", choices=["autocad-mcp-pro"])
    parser.add_argument("--backend", default="ezdxf", choices=["ezdxf", "com"])
    parser.add_argument("--task", action="append", help="Run only this task id (repeatable)")
    parser.add_argument("--artifact-dir", default="benchmarks/results/latest")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.list:
        for task in TASKS_V2:
            print(f"{task.task_id}\t{task.category}\t{task.description}")
        return

    from benchmarks.adapters.autocad_mcp_pro import AutoCADMCPProAdapter

    tasks = [task_by_id(task_id) for task_id in args.task] if args.task else list(TASKS_V2)
    adapter = AutoCADMCPProAdapter(backend=args.backend)
    report = asyncio.run(
        run_tasks(adapter, tasks, args.artifact_dir, timeout=args.timeout)
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)


if __name__ == "__main__":
    main()
