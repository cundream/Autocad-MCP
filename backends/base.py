"""Abstract base class + shared data models for AutoCAD backends."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engineering.plan_spec import (
        CritiqueFocus,
        DimStyle,
        Issue,
        LayerSetId,
        PlanSpec,
        SheetSize,
        SnapType,
    )

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class CommandResult:
    ok: bool
    payload: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"ok": self.ok}
        if self.ok:
            d["payload"] = self.payload
        else:
            d["error"] = self.error
        return d


@dataclass
class EntityInfo:
    handle: str
    type: str          # e.g. "LINE", "CIRCLE", "ARC"
    layer: str
    color: int         # ACI color (256=ByLayer)
    linetype: str
    visible: bool
    properties: dict = field(default_factory=dict)


@dataclass
class LayerInfo:
    name: str
    color: int
    linetype: str
    lineweight: float
    is_on: bool
    is_frozen: bool
    is_locked: bool
    is_current: bool


@dataclass
class BlockInfo:
    name: str
    origin: tuple[float, float]
    attribute_count: int
    entity_count: int
    is_xref: bool
    description: str = ""


@dataclass
class DrawingInfo:
    name: str
    full_path: str
    saved: bool
    entity_count: int
    layer_count: int
    block_count: int
    extents_min: tuple[float, float]
    extents_max: tuple[float, float]
    units: str
    version: str = ""
    backend: str = ""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def normalize_lineweight(lw: "float | int | None") -> "int | None":
    """Coerce a lineweight to ezdxf/COM hundredths-of-a-mm integers.

    AutoCAD and ezdxf store lineweights as integer hundredths (25 == 0.25 mm),
    plus the -1/-2/-3 sentinels (ByLayer/ByBlock/Default). Callers, however,
    mix conventions: the MCP tool boundary passes hundredths (25) while the
    engineering layer sets pass millimetres (0.25). The old ``int(0.25)``
    silently truncated millimetre values to 0 and wiped the lineweight (and with
    it the whole ISO 128 discipline). Disambiguation is unambiguous because no
    ISO 128 millimetre value exceeds 2.0 and no valid hundredth is below 5, so
    the ``(0, 2.05]`` band is always millimetres.
    """
    if lw is None:
        return None
    try:
        v = float(lw)
    except (TypeError, ValueError):
        return lw  # leave exotic / already-int values untouched
    if v < 0:
        return int(round(v))           # -1/-2/-3 sentinels
    if v == 0:
        return 0
    if v <= 2.05:
        return int(round(v * 100.0))   # millimetres -> hundredths
    return int(round(v))               # already hundredths


# ---------------------------------------------------------------------------
# Abstract backend
# ---------------------------------------------------------------------------


class AutoCADBackend(ABC):
    """All backends implement this interface."""

    # ── identity ────────────────────────────────────────────────────────────
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    # ── drawing management ───────────────────────────────────────────────────
    @abstractmethod
    async def drawing_info(self) -> DrawingInfo: ...

    @abstractmethod
    async def drawing_new(self, template: str | None = None) -> dict: ...

    @abstractmethod
    async def drawing_open(self, path: str) -> dict: ...

    @abstractmethod
    async def drawing_save(self, path: str | None = None) -> dict: ...

    @abstractmethod
    async def drawing_save_as(self, path: str, fmt: str = "dwg") -> dict: ...

    @abstractmethod
    async def drawing_export_dxf(self, path: str) -> dict: ...

    @abstractmethod
    async def drawing_export_pdf(self, path: str) -> dict: ...

    @abstractmethod
    async def drawing_purge(self) -> dict: ...

    @abstractmethod
    async def drawing_audit(self) -> dict: ...

    @abstractmethod
    async def drawing_close(self, save: bool = True) -> dict: ...

    @abstractmethod
    async def drawing_undo(self) -> dict: ...

    @abstractmethod
    async def drawing_redo(self) -> dict: ...

    # ── entity creation ──────────────────────────────────────────────────────
    @abstractmethod
    async def entity_create_line(
        self, x1: float, y1: float, x2: float, y2: float,
        z1: float = 0.0, z2: float = 0.0,
        layer: str | None = None, color: int | None = None,
        linetype: str | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_circle(
        self, cx: float, cy: float, radius: float,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_arc(
        self, cx: float, cy: float, radius: float,
        start_angle: float, end_angle: float,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_polyline(
        self, points: list[list[float]], closed: bool = False,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_text(
        self, text: str, x: float, y: float,
        height: float = 2.5, rotation: float = 0.0,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_mtext(
        self, text: str, x: float, y: float,
        width: float = 100.0, height: float = 2.5,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_hatch(
        self, pattern: str, boundary_points: list[list[float]],
        scale: float = 1.0, angle: float = 0.0,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_spline(
        self, fit_points: list[list[float]],
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_ellipse(
        self, cx: float, cy: float,
        major_x: float, major_y: float, ratio: float = 0.5,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_point(
        self, x: float, y: float,
        layer: str | None = None, color: int | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_create_block_ref(
        self, name: str, x: float, y: float,
        scale_x: float = 1.0, scale_y: float = 1.0, rotation: float = 0.0,
        layer: str | None = None,
    ) -> EntityInfo: ...

    # ── dimensions ───────────────────────────────────────────────────────────
    @abstractmethod
    async def dimension_linear(
        self, x1: float, y1: float, x2: float, y2: float,
        dim_x: float, dim_y: float, rotation: float = 0.0,
        layer: str | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def dimension_aligned(
        self, x1: float, y1: float, x2: float, y2: float,
        dim_x: float, dim_y: float,
        layer: str | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def dimension_angular(
        self, vx: float, vy: float,
        x1: float, y1: float, x2: float, y2: float,
        tx: float, ty: float,
        layer: str | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def dimension_radius(
        self, cx: float, cy: float, chord_x: float, chord_y: float,
        leader_length: float = 10.0, layer: str | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def dimension_diameter(
        self, x1: float, y1: float, x2: float, y2: float,
        leader_length: float = 10.0, layer: str | None = None,
    ) -> EntityInfo: ...

    # ── entity modification ──────────────────────────────────────────────────
    @abstractmethod
    async def entity_move(self, handle: str, dx: float, dy: float, dz: float = 0.0) -> dict: ...

    @abstractmethod
    async def entity_copy(self, handle: str, dx: float, dy: float, dz: float = 0.0) -> EntityInfo: ...

    @abstractmethod
    async def entity_rotate(
        self, handle: str, base_x: float, base_y: float, angle_deg: float,
    ) -> dict: ...

    @abstractmethod
    async def entity_scale(
        self, handle: str, base_x: float, base_y: float, factor: float,
    ) -> dict: ...

    @abstractmethod
    async def entity_mirror(
        self, handle: str,
        x1: float, y1: float, x2: float, y2: float,
        delete_original: bool = False,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_offset(
        self, handle: str, distance: float,
        side_x: float | None = None, side_y: float | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def entity_delete(self, handle: str) -> dict: ...

    @abstractmethod
    async def entity_array_rectangular(
        self, handle: str,
        rows: int, cols: int, row_spacing: float, col_spacing: float,
    ) -> list[EntityInfo]: ...

    @abstractmethod
    async def entity_array_polar(
        self, handle: str,
        count: int, fill_angle: float,
        center_x: float, center_y: float,
    ) -> list[EntityInfo]: ...

    # ── corner operations (trim/extend/fillet/chamfer) ───────────────────────
    @abstractmethod
    async def entity_trim(
        self, target_handle: str, cutter_handle: str,
        keep_x: float, keep_y: float,
    ) -> EntityInfo:
        """Trim `target` against `cutter`; keep the segment containing
        (keep_x, keep_y). Raises ToolError if no intersection."""
        ...

    @abstractmethod
    async def entity_extend(
        self, target_handle: str, boundary_handle: str,
        end_x: float | None = None, end_y: float | None = None,
    ) -> EntityInfo:
        """Extend `target` to meet `boundary`. If `end_x/y` is None, the
        target endpoint nearest the boundary is auto-selected."""
        ...

    @abstractmethod
    async def entity_fillet(
        self, handle1: str, handle2: str, radius: float,
        trim: bool = True,
    ) -> EntityInfo:
        """Fillet two entities with the given radius. Returns the new ARC.
        When `trim` is True (default), the source entities are shortened
        to the tangent points (AutoCAD default behaviour)."""
        ...

    @abstractmethod
    async def entity_chamfer(
        self, handle1: str, handle2: str,
        dist1: float, dist2: float | None = None,
        trim: bool = True,
    ) -> EntityInfo:
        """Chamfer two entities. When `dist2` is None it defaults to `dist1`
        (symmetric chamfer). Returns the new chamfer LINE."""
        ...

    # ── entity query/properties ───────────────────────────────────────────────
    @abstractmethod
    async def entity_get(self, handle: str) -> EntityInfo: ...

    @abstractmethod
    async def entity_set_properties(
        self, handle: str,
        layer: str | None = None,
        color: int | None = None,
        linetype: str | None = None,
        lineweight: float | None = None,
        visible: bool | None = None,
    ) -> dict: ...

    @abstractmethod
    async def entity_list(
        self,
        type_filter: str | None = None,
        layer_filter: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[EntityInfo]: ...

    # ── layer management ─────────────────────────────────────────────────────
    @abstractmethod
    async def layer_list(self) -> list[LayerInfo]: ...

    @abstractmethod
    async def layer_create(
        self, name: str,
        color: int = 7,
        linetype: str = "Continuous",
        lineweight: float = -3,
    ) -> LayerInfo: ...

    @abstractmethod
    async def layer_delete(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_set_current(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_modify(
        self, name: str,
        color: int | None = None,
        linetype: str | None = None,
        lineweight: float | None = None,
    ) -> LayerInfo: ...

    @abstractmethod
    async def layer_freeze(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_thaw(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_lock(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_unlock(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_hide(self, name: str) -> dict: ...

    @abstractmethod
    async def layer_show(self, name: str) -> dict: ...

    # ── linetype management ──────────────────────────────────────────────────
    @abstractmethod
    async def linetype_list(self) -> list[str]: ...

    @abstractmethod
    async def linetype_load(
        self, name: str, file: str | None = None,
    ) -> dict: ...

    # ── block operations ─────────────────────────────────────────────────────
    @abstractmethod
    async def block_list(self) -> list[BlockInfo]: ...

    @abstractmethod
    async def block_insert(
        self, name: str, x: float, y: float,
        scale_x: float = 1.0, scale_y: float = 1.0, rotation: float = 0.0,
        attributes: dict | None = None,
        layer: str | None = None,
    ) -> EntityInfo: ...

    @abstractmethod
    async def block_explode(self, handle: str) -> dict: ...

    @abstractmethod
    async def block_get_attributes(self, handle: str) -> dict: ...

    @abstractmethod
    async def block_set_attributes(self, handle: str, attributes: dict) -> dict: ...

    @abstractmethod
    async def block_create_from_entities(
        self, name: str, handles: list[str],
        base_x: float = 0.0, base_y: float = 0.0,
    ) -> dict: ...

    # ── analysis / query ─────────────────────────────────────────────────────
    @abstractmethod
    async def analysis_stats(self) -> dict: ...

    @abstractmethod
    async def analysis_entities_in_region(
        self, x1: float, y1: float, x2: float, y2: float,
    ) -> list[EntityInfo]: ...

    @abstractmethod
    async def analysis_measure_distance(
        self, x1: float, y1: float, x2: float, y2: float,
    ) -> float: ...

    @abstractmethod
    async def analysis_measure_area(self, points: list[list[float]]) -> float: ...

    @abstractmethod
    async def analysis_bounding_box(self) -> dict: ...

    @abstractmethod
    async def analysis_select_by_layer(self, layer_name: str) -> list[EntityInfo]: ...

    @abstractmethod
    async def analysis_select_by_type(self, entity_type: str) -> list[EntityInfo]: ...

    # ── view / screenshot ────────────────────────────────────────────────────
    @abstractmethod
    async def view_zoom_extents(self) -> dict: ...

    @abstractmethod
    async def view_zoom_window(
        self, x1: float, y1: float, x2: float, y2: float,
    ) -> dict: ...

    @abstractmethod
    async def view_screenshot(self) -> bytes | None: ...

    # ── transactions ─────────────────────────────────────────────────────────
    @abstractmethod
    async def transaction_begin(self) -> dict: ...

    @abstractmethod
    async def transaction_commit(self) -> dict: ...

    @abstractmethod
    async def transaction_rollback(self) -> dict: ...

    # ── system ───────────────────────────────────────────────────────────────
    @abstractmethod
    async def system_status(self) -> dict: ...

    @abstractmethod
    async def system_get_variable(self, name: str) -> Any: ...

    @abstractmethod
    async def system_set_variable(self, name: str, value: Any) -> dict: ...

    @abstractmethod
    async def system_run_command(self, command: str) -> dict: ...

    @abstractmethod
    async def system_run_lisp(self, expression: str) -> dict: ...

    # ── premium meta-tools (planning + critique + snap + construction) ──────
    # These are CONCRETE and backend-agnostic: they orchestrate the abstract
    # primitives above plus the shared EntityInfo.properties contract (start/
    # end/center/radius/start_angle/end_angle — populated identically by both
    # backends), so the ezdxf and COM backends inherit identical premium
    # behaviour. The only backend-specific primitive is `_create_xline` — XLINE
    # has no cross-backend equivalent among the standard entity_create_* tools.

    _plan_spec: "PlanSpec | None" = None

    async def drawing_plan(
        self, intent: str,
        sheet_size: "SheetSize" = "A3",
        scale: float = 1.0,
        layer_set_id: "LayerSetId" = "mech",
        view_count: int = 1,
        dim_style: "DimStyle" = "chain",
        notes: list[str] | None = None,
    ) -> "PlanSpec":
        """Commit a drawing intent before any geometry is created.
        Returns a PlanSpec held on the backend for `drawing_critique`."""
        from engineering.plan_spec import PlanSpec
        plan = PlanSpec(
            intent=str(intent),
            sheet_size=sheet_size,
            scale=float(scale),
            layer_set_id=layer_set_id,
            view_count=int(view_count),
            dim_style=dim_style,
            notes=list(notes) if notes else [],
        )
        self._plan_spec = plan
        return plan

    async def drawing_critique(
        self, focus: list["CritiqueFocus"] | None = None,
    ) -> list["Issue"]:
        """Run premium-quality checks; return zero issues before
        `drawing_finalize`. `focus=None` runs all checks."""
        from engineering.critique import run_critique
        return await run_critique(self, focus)

    async def point_from_snap(
        self, handle: str, snap: "SnapType",
        ref_x: float | None = None, ref_y: float | None = None,
    ) -> tuple[float, float]:
        """Return a deterministic snap point on `handle`.
        snap ∈ {end, mid, center, quad, perp, near}. For `near/perp`,
        `ref_x/y` is the reference point. Sources geometry from the shared
        EntityInfo.properties contract — works on every backend."""
        ent = await self.entity_get(handle)
        et = ent.type
        p = ent.properties
        ref = (
            (float(ref_x), float(ref_y))
            if ref_x is not None and ref_y is not None else None
        )

        def _line_pts():
            s = p.get("start")
            e = p.get("end")
            if s is None or e is None:
                raise RuntimeError(
                    f"point_from_snap: entity {handle} ({et}) has no start/end."
                )
            return (float(s[0]), float(s[1])), (float(e[0]), float(e[1]))

        def _circle_geom():
            c = p.get("center")
            r = p.get("radius")
            if c is None or r is None:
                raise RuntimeError(
                    f"point_from_snap: entity {handle} ({et}) has no center/radius."
                )
            return float(c[0]), float(c[1]), float(r)

        if snap == "end":
            if et == "LINE":
                s, e = _line_pts()
                if ref is None:
                    return s
                ds = (s[0] - ref[0]) ** 2 + (s[1] - ref[1]) ** 2
                de = (e[0] - ref[0]) ** 2 + (e[1] - ref[1]) ** 2
                return s if ds <= de else e
            if et == "ARC":
                cx, cy, r = _circle_geom()
                sa = math.radians(float(p["start_angle"]))
                ea = math.radians(float(p["end_angle"]))
                sp = (cx + r * math.cos(sa), cy + r * math.sin(sa))
                ep = (cx + r * math.cos(ea), cy + r * math.sin(ea))
                if ref is None:
                    return sp
                ds = (sp[0] - ref[0]) ** 2 + (sp[1] - ref[1]) ** 2
                de = (ep[0] - ref[0]) ** 2 + (ep[1] - ref[1]) ** 2
                return sp if ds <= de else ep
            raise RuntimeError(f"point_from_snap: 'end' snap not supported on {et}")

        if snap == "mid":
            if et == "LINE":
                s, e = _line_pts()
                return ((s[0] + e[0]) / 2.0, (s[1] + e[1]) / 2.0)
            if et == "ARC":
                cx, cy, r = _circle_geom()
                sa = math.radians(float(p["start_angle"]))
                ea = math.radians(float(p["end_angle"]))
                if ea < sa:
                    ea += 2 * math.pi
                ma = (sa + ea) / 2.0
                return (cx + r * math.cos(ma), cy + r * math.sin(ma))
            raise RuntimeError(f"point_from_snap: 'mid' snap not supported on {et}")

        if snap == "center":
            if et in ("CIRCLE", "ARC", "ELLIPSE"):
                c = p.get("center")
                if c is None:
                    raise RuntimeError(
                        f"point_from_snap: entity {handle} ({et}) has no center."
                    )
                return (float(c[0]), float(c[1]))
            raise RuntimeError(f"point_from_snap: 'center' snap not supported on {et}")

        if snap == "quad":
            if et in ("CIRCLE", "ARC"):
                cx, cy, r = _circle_geom()
                pts = [(cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
                if ref is None:
                    return pts[0]
                return min(pts, key=lambda q: (q[0] - ref[0]) ** 2 + (q[1] - ref[1]) ** 2)
            raise RuntimeError(f"point_from_snap: 'quad' snap not supported on {et}")

        if snap == "perp":
            if ref is None:
                raise RuntimeError("point_from_snap: 'perp' requires ref_x/ref_y.")
            if et == "LINE":
                s, e = _line_pts()
                dx = e[0] - s[0]
                dy = e[1] - s[1]
                L2 = dx * dx + dy * dy
                if L2 < 1e-18:
                    raise RuntimeError("point_from_snap: line has zero length.")
                t = ((ref[0] - s[0]) * dx + (ref[1] - s[1]) * dy) / L2
                return (s[0] + t * dx, s[1] + t * dy)
            raise RuntimeError(f"point_from_snap: 'perp' snap not supported on {et}")

        if snap == "near":
            if ref is None:
                raise RuntimeError("point_from_snap: 'near' requires ref_x/ref_y.")
            if et == "LINE":
                s, e = _line_pts()
                dx = e[0] - s[0]
                dy = e[1] - s[1]
                L2 = dx * dx + dy * dy
                if L2 < 1e-18:
                    return s
                t = ((ref[0] - s[0]) * dx + (ref[1] - s[1]) * dy) / L2
                t = max(0.0, min(1.0, t))
                return (s[0] + t * dx, s[1] + t * dy)
            if et in ("CIRCLE", "ARC"):
                cx, cy, r = _circle_geom()
                vx, vy = ref[0] - cx, ref[1] - cy
                L = math.hypot(vx, vy)
                if L < 1e-18:
                    return (cx + r, cy)
                return (cx + r * vx / L, cy + r * vy / L)
            raise RuntimeError(f"point_from_snap: 'near' snap not supported on {et}")

        if snap == "int":
            raise RuntimeError(
                "point_from_snap: 'int' (intersection) requires a 2nd entity; "
                "compute via two endpoints. V2 will accept a 2nd handle."
            )

        raise RuntimeError(
            f"point_from_snap: unknown snap type '{snap}'. "
            "Use one of: end, mid, center, quad, perp, near."
        )

    @abstractmethod
    async def _create_xline(
        self, x: float, y: float, dx: float, dy: float, layer: str,
    ) -> EntityInfo:
        """Create an infinite construction line (XLINE) through (x, y) with
        unit direction (dx, dy) on `layer`. Backend-specific: XLINE has no
        cross-backend entity_create_* equivalent."""
        ...

    async def _ensure_layer(self, name: str, color: int = 7) -> None:
        """Idempotently make sure `name` exists (no-op if already present)."""
        try:
            existing = {lyr.name for lyr in await self.layer_list()}
        except Exception:
            existing = set()
        if name not in existing:
            try:
                await self.layer_create(name, color=color)
            except Exception:
                pass  # already created / racy create — harmless

    async def construction_xline(
        self, x: float, y: float, angle_deg: float,
        layer: str = "CONSTRUCTION",
    ) -> EntityInfo:
        """Create an infinite construction line (XLINE) on a CONSTRUCTION
        layer (auto-created with color 250 = lightest if missing)."""
        await self._ensure_layer(layer, color=250)
        ang = math.radians(float(angle_deg))
        return await self._create_xline(
            float(x), float(y), math.cos(ang), math.sin(ang), layer,
        )

    async def construction_clear(
        self, layer: str = "CONSTRUCTION",
    ) -> dict:
        """Delete every entity on the CONSTRUCTION layer.
        Must be called before `drawing_finalize`."""
        try:
            ents = await self.entity_list(layer_filter=layer, limit=5000)
        except Exception:
            ents = []
        deleted = 0
        for ent in ents:
            try:
                await self.entity_delete(ent.handle)
                deleted += 1
            except Exception:
                continue
        return {"ok": True, "layer": layer, "deleted": deleted}

    async def drawing_apply_iso_layers(
        self, standard: "LayerSetId" = "mech",
    ) -> dict:
        """Bootstrap a full ISO-conformant layer set with correct colors
        and lineweights. Idempotent."""
        from engineering.layers import apply_layer_set
        result = await apply_layer_set(self, standard)
        return {"ok": True, "standard": standard, "layers": result}

    async def dimension_auto(
        self, handles: list[str], style: "DimStyle" = "chain",
        offset: float = 10.0,
    ) -> list[EntityInfo]:
        """Generate ISO 129 dimensions across `handles` in the chosen style
        (chain | baseline | ordinate). `offset` is the dimension-line
        distance from the reference geometry (mm)."""
        if not handles:
            return []
        if style not in ("chain", "baseline", "ordinate"):
            raise RuntimeError(
                f"dimension_auto: unknown style '{style}'. "
                "Use 'chain', 'baseline', or 'ordinate'."
            )
        segs: list[tuple[float, float, float, float]] = []
        for h in handles:
            ent = await self.entity_get(h)
            if ent.type != "LINE":
                raise RuntimeError(
                    f"dimension_auto V1: only LINE entities supported "
                    f"(handle {h} is {ent.type})."
                )
            s = ent.properties.get("start")
            e = ent.properties.get("end")
            if s is None or e is None:
                raise RuntimeError(f"dimension_auto: line {h} missing start/end.")
            segs.append((float(s[0]), float(s[1]), float(e[0]), float(e[1])))

        off = float(offset)
        results: list[EntityInfo] = []

        if style == "chain":
            # Each line gets its own linear (rotated) dimension, offset clear of
            # the geometry along its own perpendicular.
            for sx, sy, ex, ey in segs:
                mx = (sx + ex) / 2.0
                my = (sy + ey) / 2.0
                dx, dy = ex - sx, ey - sy
                L = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / L, dx / L
                dim = await self.dimension_linear(
                    sx, sy, ex, ey, mx + nx * off, my + ny * off,
                    rotation=math.degrees(math.atan2(dy, dx)), layer="DIM",
                )
                results.append(dim)

        elif style == "baseline":
            sx0, sy0, ex0, ey0 = segs[0]
            dx, dy = ex0 - sx0, ey0 - sy0
            L0 = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L0, dy / L0
            for i, (sx, sy, ex, ey) in enumerate(segs):
                dim = await self.dimension_linear(
                    sx0, sy0, ex, ey,
                    sx0 - uy * (off + i * off), sy0 + ux * (off + i * off),
                    layer="DIM",
                )
                results.append(dim)

        else:  # ordinate — X then Y distance of each segment's end from start
            for sx, sy, ex, ey in segs:
                if abs(ex - sx) > 1e-9:
                    dim = await self.dimension_linear(
                        sx, sy, ex, sy,
                        sx + (ex - sx) / 2.0, max(sy, ey) + off, layer="DIM",
                    )
                    results.append(dim)
                if abs(ey - sy) > 1e-9:
                    dim = await self.dimension_linear(
                        ex, sy, ex, ey,
                        max(sx, ex) + off, (sy + ey) / 2.0,
                        rotation=90.0, layer="DIM",
                    )
                    results.append(dim)

        return results

    async def entity_select_smart(
        self, predicate: dict,
    ) -> list[EntityInfo]:
        """Semantic entity selection. Predicate keys (all optional, AND-ed):
        - type: "LINE" | "CIRCLE" | ...
        - layer: layer name
        - near: [x, y, radius] — entity reference point within circle
        - length_range: [min, max] — applies to LINE/ARC
        - color: ACI int
        """
        if not isinstance(predicate, dict):
            raise RuntimeError("entity_select_smart: predicate must be a dict.")
        ptype = predicate.get("type")
        player = predicate.get("layer")
        pnear = predicate.get("near")          # [x, y, radius]
        plen = predicate.get("length_range")   # [min, max]
        pcolor = predicate.get("color")

        ents = await self.entity_list(
            type_filter=ptype.upper() if isinstance(ptype, str) else None,
            layer_filter=player if isinstance(player, str) else None,
            limit=5000,
        )

        def _ok(e: EntityInfo) -> bool:
            if pcolor is not None and int(e.color) != int(pcolor):
                return False
            if pnear is not None:
                try:
                    nx, ny, nr = float(pnear[0]), float(pnear[1]), float(pnear[2])
                except Exception:
                    return False
                pt = (e.properties.get("start")
                      or e.properties.get("center")
                      or e.properties.get("insertion")
                      or e.properties.get("insertion_point"))
                if pt is None:
                    return False
                if (float(pt[0]) - nx) ** 2 + (float(pt[1]) - ny) ** 2 > nr ** 2:
                    return False
            if plen is not None and e.type in ("LINE", "ARC"):
                try:
                    lmin, lmax = float(plen[0]), float(plen[1])
                except Exception:
                    return False
                length = e.properties.get("length")
                if length is None or not (lmin <= float(length) <= lmax):
                    return False
            return True

        return [e for e in ents if _ok(e)]

    # ── concrete helpers (use existing primitives) ──────────────────────────
    async def set_layer_active(self, name: str) -> None:
        """Convenience: alias for layer_set_current. Concrete; backends need not override."""
        await self.layer_set_current(name)

    async def ensure_linetypes(
        self, names: list[str], file: str | None = None,
    ) -> dict[str, str]:
        """Idempotently load each linetype in `names`. Returns {name: status}.
        Status is one of: 'already_loaded', 'loaded', 'failed: <msg>'.
        """
        try:
            current = {ln.lower() for ln in await self.linetype_list()}
        except Exception:
            current = set()
        results: dict[str, str] = {}
        for n in names:
            if n.lower() in current:
                results[n] = "already_loaded"
                continue
            try:
                await self.linetype_load(n, file=file)
                results[n] = "loaded"
            except Exception as exc:
                results[n] = f"failed: {exc}"
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def shoelace_area(points: list[list[float]]) -> float:
    """Calculate polygon area using the shoelace formula."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0


def deg2rad(degrees: float) -> float:
    return degrees * math.pi / 180.0


def rad2deg(radians: float) -> float:
    return radians * 180.0 / math.pi
