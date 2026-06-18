"""Deterministic engineering CAD layer for AutoCAD MCP Pro."""

from .gear import (
    draw_gear_section_aa,
    draw_helical_gear_front_view,
    draw_spur_gear_front_view,
    generate_full_gear_outline,
    generate_involute_flank,
    involute_xy,
)
from .keyway import (
    DIN6885_TABLE,
    draw_keyed_bore,
    draw_keyway_section,
    keyway_dimensions,
)
from .layers import (
    ENGINEERING_LAYERS,
    STANDARD_LINETYPES,
    ensure_engineering_layers,
    ensure_standard_linetypes,
)
from .plan_spec import (
    ALL_CRITIQUE_FOCUSES,
    ISO_128_LINEWEIGHTS_MM,
    CritiqueFocus,
    DimStyle,
    Issue,
    LayerSetId,
    PlanSpec,
    SheetSize,
    SnapType,
)
from .titleblock import TitleBlockMetadata, apply_iso_a3_titleblock
from .validator import DrawingValidator, ValidationFinding, ValidationResult

__all__ = [
    "draw_helical_gear_front_view",
    "draw_spur_gear_front_view",
    "draw_gear_section_aa",
    "generate_full_gear_outline",
    "generate_involute_flank",
    "involute_xy",
    "draw_keyed_bore",
    "draw_keyway_section",
    "keyway_dimensions",
    "DIN6885_TABLE",
    "ENGINEERING_LAYERS",
    "STANDARD_LINETYPES",
    "ensure_engineering_layers",
    "ensure_standard_linetypes",
    "apply_iso_a3_titleblock",
    "TitleBlockMetadata",
    "DrawingValidator",
    "ValidationResult",
    "ValidationFinding",
    "PlanSpec",
    "Issue",
    "CritiqueFocus",
    "SheetSize",
    "LayerSetId",
    "DimStyle",
    "SnapType",
    "ALL_CRITIQUE_FOCUSES",
    "ISO_128_LINEWEIGHTS_MM",
]
