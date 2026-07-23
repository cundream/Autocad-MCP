"""ISO 286 fit-table lookups pinned against published table values."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from engineering.fits import FitDeviation, fit_lookup, parse_fit_code
from engineering.tolerances import build_dim_override
from server import _fit_to_tolerances


def _um(value_mm: float) -> float:
    return round(value_mm * 1000.0, 3)


# (code, nominal, upper µm, lower µm) — published ISO 286-2 values.
CANONICAL_FITS = [
    ("H7", 20.0, 21, 0),
    ("H7", 40.0, 25, 0),
    ("H8", 30.0, 33, 0),
    ("H9", 6.0, 30, 0),
    ("H7", 200.0, 46, 0),
    ("g6", 20.0, -7, -20),
    ("g6", 6.0, -4, -12),
    ("f7", 40.0, -25, -50),
    ("e8", 25.0, -40, -73),
    ("d9", 100.0, -120, -207),
    ("h6", 30.0, 0, -13),  # 30 mm is inside the >18-30 step (inclusive upper bound)
    ("h7", 50.0, 0, -25),
    ("k6", 20.0, 15, 2),
    ("m6", 25.0, 21, 8),
    ("n6", 20.0, 28, 15),
    ("p6", 20.0, 35, 22),
    ("js9", 25.0, 26, -26),
    ("G7", 6.0, 16, 4),
    ("F8", 40.0, 64, 25),
    ("D10", 30.0, 149, 65),
]


@pytest.mark.parametrize("code,nominal,upper_um,lower_um", CANONICAL_FITS)
def test_canonical_fit_values(code, nominal, upper_um, lower_um):
    deviation = fit_lookup(code, nominal)
    assert isinstance(deviation, FitDeviation)
    assert _um(deviation.upper_mm) == pytest.approx(upper_um), f"{code}@{nominal} upper"
    assert _um(deviation.lower_mm) == pytest.approx(lower_um), f"{code}@{nominal} lower"


def test_k_outside_it4_to_7_has_zero_lower_deviation():
    deviation = fit_lookup("k9", 20.0)
    assert deviation.lower_mm == 0.0
    assert _um(deviation.upper_mm) == 52  # IT9 @ 18-30


def test_parse_fit_code():
    assert parse_fit_code("H7") == ("H", 7)
    assert parse_fit_code("js10") == ("js", 10)
    with pytest.raises(ValueError):
        parse_fit_code("77")
    with pytest.raises(ValueError):
        parse_fit_code("")


@pytest.mark.parametrize(
    "code,nominal",
    [
        ("K7", 20.0),  # transition hole letters need the delta-rule — excluded
        ("P7", 20.0),
        ("x6", 20.0),  # letter outside the authored subset (regex rejects)
        ("H3", 20.0),  # grade below authored range
        ("H12", 20.0),  # grade above authored range
        ("H7", 0.5),  # below 1 mm
        ("H7", 600.0),  # above 500 mm
    ],
)
def test_out_of_scope_lookups_raise(code, nominal):
    with pytest.raises(ValueError):
        fit_lookup(code, nominal)


def test_double_positive_fit_renders_correct_dimvars():
    """p6-style fits (+upper/+lower) must produce a negative DIMTM so AutoCAD
    displays the plus lower deviation."""
    deviation = fit_lookup("p6", 20.0)
    override, _ = build_dim_override(
        tol_upper=deviation.upper_mm,
        tol_lower=-deviation.lower_mm,  # server convention: positive = minus
        tol_mode="deviation",
    )
    assert override["dimtp"] == pytest.approx(0.035)
    assert override["dimtm"] == pytest.approx(-0.022)  # displayed as +0.022


def test_fit_to_tolerances_contract():
    tol_upper, tol_lower, tol_mode, text = _fit_to_tolerances("H7", 20.0, None, None, "none", None)
    assert tol_upper == pytest.approx(0.021)
    assert tol_lower == pytest.approx(0.0)
    assert tol_mode == "deviation"
    assert text == "<> H7"


def test_fit_to_tolerances_rejects_mixed_usage():
    with pytest.raises(ToolError):
        _fit_to_tolerances("H7", 20.0, 0.1, None, "none", None)
    with pytest.raises(ToolError):
        _fit_to_tolerances("H7", 20.0, None, None, "symmetric", None)
    with pytest.raises(ToolError):
        _fit_to_tolerances("Q9", 20.0, None, None, "none", None)


def test_fit_passthrough_without_code():
    assert _fit_to_tolerances(None, 20.0, 0.1, 0.05, "deviation", "x") == (
        0.1,
        0.05,
        "deviation",
        "x",
    )
