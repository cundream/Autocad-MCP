"""Premium-quality critique checks for finished drawings.

Each focus runs an independent check; new focuses must be added to the
`CritiqueFocus` Literal in plan_spec.py *and* registered here. Closed enum
keeps drawing_critique scope from drifting.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .layers import ENGINEERING_LAYERS
from .plan_spec import (
    ALL_CRITIQUE_FOCUSES,
    ISO_128_LINEWEIGHTS_MM,
    CritiqueFocus,
    Issue,
)

if TYPE_CHECKING:
    from backends.base import AutoCADBackend


# Layer-name → expected ACI color, derived from ENGINEERING_LAYERS.
_EXPECTED_LAYER_COLOR: dict[str, int] = {
    name: color for name, color, _lt, _lw, _desc in ENGINEERING_LAYERS
}

# Dimension entity types that should sit on the DIM layer.
_DIM_TYPES = {
    "DIMENSION", "DIMLINEAR", "DIMALIGNED", "DIMANGULAR",
    "DIMRADIUS", "DIMDIAMETER", "DIMORDINATE",
}


async def _check_iso128(backend: "AutoCADBackend") -> list[Issue]:
    """Layer lineweights must be in ISO_128_LINEWEIGHTS_MM (or -3=ByLayer
    sentinel meaning 'inherit')."""
    issues: list[Issue] = []
    try:
        layers = await backend.layer_list()
    except Exception as exc:
        return [Issue("warning", "iso128", f"layer_list failed: {exc}")]
    allowed = set(ISO_128_LINEWEIGHTS_MM)
    for lyr in layers:
        lw = float(lyr.lineweight)
        # AutoCAD sentinels: -1 (Default), -2 (ByBlock), -3 (ByLayer);
        # 0.0 = ezdxf's "use default" — not an ISO 128 violation.
        if lw <= 0:
            continue
        # ezdxf returns lineweight in mm-hundredths (e.g. 25 = 0.25mm) for
        # some entity properties; the layer dataclass already normalises to mm.
        if lw not in allowed and (lw / 100.0) not in allowed:
            issues.append(Issue(
                severity="warning",
                focus="iso128",
                message=(
                    f"Layer '{lyr.name}' lineweight {lw} mm is not in the "
                    f"ISO 128 set {sorted(allowed)}."
                ),
                detail={"layer": lyr.name, "lineweight": lw},
            ))
    return issues


async def _check_layer_color(backend: "AutoCADBackend") -> list[Issue]:
    """Engineering-standard layers must keep their canonical ACI color."""
    issues: list[Issue] = []
    try:
        layers = await backend.layer_list()
    except Exception:
        return []
    for lyr in layers:
        expected = _EXPECTED_LAYER_COLOR.get(lyr.name)
        if expected is None:
            continue   # unknown layer — caller's responsibility
        if int(lyr.color) != int(expected):
            issues.append(Issue(
                severity="warning",
                focus="layer_color",
                message=(
                    f"Layer '{lyr.name}' has color {lyr.color}; "
                    f"engineering standard expects {expected}."
                ),
                detail={"layer": lyr.name, "got": int(lyr.color), "expected": expected},
            ))
    return issues


async def _check_construction_left(backend: "AutoCADBackend") -> list[Issue]:
    """CONSTRUCTION layer must be empty before drawing_finalize."""
    try:
        ents = await backend.entity_list(layer_filter="CONSTRUCTION", limit=5000)
    except Exception:
        return []
    if not ents:
        return []
    return [Issue(
        severity="error",
        focus="construction_left",
        message=(
            f"{len(ents)} entity/entities still on CONSTRUCTION layer. "
            "Call construction_clear() before drawing_finalize."
        ),
        handles=[e.handle for e in ents[:50]],
        detail={"count": len(ents)},
    )]


async def _check_untrimmed_corner(backend: "AutoCADBackend") -> list[Issue]:
    """Two LINE endpoints within `tol` but not exactly equal usually means a
    corner where one line overshoots — TRIM/EXTEND/FILLET was forgotten."""
    tol = 0.5  # mm — generous; tighten via PlanSpec.notes later
    try:
        lines = await backend.entity_list(type_filter="LINE", limit=5000)
    except Exception:
        return []
    endpoints: list[tuple[str, tuple[float, float]]] = []
    for ln in lines:
        s = ln.properties.get("start")
        e = ln.properties.get("end")
        if s and e:
            endpoints.append((ln.handle, (float(s[0]), float(s[1]))))
            endpoints.append((ln.handle, (float(e[0]), float(e[1]))))
    issues: list[Issue] = []
    n = len(endpoints)
    seen: set[frozenset[str]] = set()
    for i in range(n):
        h1, p1 = endpoints[i]
        for j in range(i + 1, n):
            h2, p2 = endpoints[j]
            if h1 == h2:
                continue
            d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if 1e-9 < d <= tol:
                key = frozenset((h1, h2))
                if key in seen:
                    continue
                seen.add(key)
                issues.append(Issue(
                    severity="warning",
                    focus="untrimmed_corner",
                    message=(
                        f"Lines {h1} and {h2} have endpoints {d:.3f} mm apart — "
                        "likely an untrimmed corner (use entity_trim or entity_fillet)."
                    ),
                    handles=[h1, h2],
                    detail={"gap_mm": d, "p1": list(p1), "p2": list(p2)},
                ))
    return issues


async def _check_duplicate_entities(backend: "AutoCADBackend") -> list[Issue]:
    """Two LINEs with identical endpoints (in either direction) are duplicates."""
    try:
        lines = await backend.entity_list(type_filter="LINE", limit=5000)
    except Exception:
        return []
    seen: dict[tuple, str] = {}
    issues: list[Issue] = []
    for ln in lines:
        s = ln.properties.get("start")
        e = ln.properties.get("end")
        if not (s and e):
            continue
        k1 = (round(s[0], 4), round(s[1], 4), round(e[0], 4), round(e[1], 4))
        k2 = (k1[2], k1[3], k1[0], k1[1])
        for key in (k1, k2):
            if key in seen:
                issues.append(Issue(
                    severity="warning",
                    focus="duplicate_entities",
                    message=f"Lines {seen[key]} and {ln.handle} are duplicates.",
                    handles=[seen[key], ln.handle],
                ))
                break
        else:
            seen[k1] = ln.handle
    return issues


async def _check_dim_overlap(backend: "AutoCADBackend") -> list[Issue]:
    """Two dimensions whose insertion points are within `tol` likely overlap."""
    tol = 5.0  # mm
    try:
        ents = await backend.entity_list(layer_filter="DIM", limit=5000)
    except Exception:
        return []
    dim_points: list[tuple[str, tuple[float, float]]] = []
    for e in ents:
        if e.type not in _DIM_TYPES and "DIM" not in e.type:
            continue
        ip = (e.properties.get("text_position")
              or e.properties.get("defpoint")
              or e.properties.get("insertion_point"))
        if ip and len(ip) >= 2:
            dim_points.append((e.handle, (float(ip[0]), float(ip[1]))))
    issues: list[Issue] = []
    seen: set[frozenset[str]] = set()
    for i, (h1, p1) in enumerate(dim_points):
        for j in range(i + 1, len(dim_points)):
            h2, p2 = dim_points[j]
            d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if d <= tol:
                key = frozenset((h1, h2))
                if key in seen:
                    continue
                seen.add(key)
                issues.append(Issue(
                    severity="warning",
                    focus="dim_overlap",
                    message=f"Dimensions {h1} and {h2} are {d:.2f} mm apart — likely overlapping.",
                    handles=[h1, h2],
                ))
    return issues


_FOCUS_DISPATCH = {
    "iso128": _check_iso128,
    "layer_color": _check_layer_color,
    "dim_overlap": _check_dim_overlap,
    "untrimmed_corner": _check_untrimmed_corner,
    "duplicate_entities": _check_duplicate_entities,
    "construction_left": _check_construction_left,
}


async def run_critique(
    backend: "AutoCADBackend",
    focus: list[CritiqueFocus] | None = None,
) -> list[Issue]:
    """Dispatch each requested focus check and return aggregated issues."""
    foci = list(focus) if focus is not None else list(ALL_CRITIQUE_FOCUSES)
    issues: list[Issue] = []
    for f in foci:
        check = _FOCUS_DISPATCH.get(f)
        if check is None:
            issues.append(Issue(
                severity="warning",
                focus=f,  # type: ignore[arg-type]
                message=f"Unknown critique focus '{f}' (closed enum).",
            ))
            continue
        issues.extend(await check(backend))
    return issues
