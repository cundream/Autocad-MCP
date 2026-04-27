# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Security module (`security.py`) with path traversal protection and command injection prevention
- Centralized configuration (`config.py`) with environment variable support
- `.env.example` for environment variable documentation
- Path validation for all file operations (`drawing_open`, `drawing_save`, `drawing_export_*`)
- Command sanitization for `system_run_command` and `system_run_lisp`
- Ruff linting configuration in `pyproject.toml`
- Pre-commit hooks (`.pre-commit-config.yaml`) for automated code quality
- pytest-cov for test coverage reporting
- Comprehensive test suite: 95 tests across 7 test files
  - `test_entity_creation.py` — 13 entity creation tests
  - `test_drawing.py` — 8 drawing operation tests
  - `test_dimensions.py` — 5 dimension tests
  - `test_layer_block.py` — 12 layer and block tests
  - `test_analysis.py` — 12 analysis and modification tests
  - `test_security.py` — 29 security tests
- GitHub Actions CI workflow (lint + test on Python 3.11/3.12)
- README.md with full documentation
- CHANGELOG.md
- `.gitignore`

### Changed
- All silent `except Exception: pass` blocks now include logging
- Removed unused imports across all source files
- Renamed ambiguous variable `l` to `lyr` in layer iteration code
- Import sorting organized with ruff isort rules

### Fixed
- `_detect_autocad_running` now logs detection failures instead of silently swallowing them
- Resource functions now log errors before returning error JSON

## [1.0.0] — 2026-03-01

### Added
- Initial release with 67 tools, 6 resources, 5 prompt templates
- Dual-engine architecture: COM backend (live AutoCAD) + ezdxf backend (headless)
- FastMCP 3.0 server with middleware stack (error handling, audit, timing, logging)
- Drawing management: new, open, save, save-as, export DXF/PDF, purge, audit, undo/redo
- Entity creation: line, circle, arc, polyline, rectangle, text, mtext, hatch, spline, ellipse, point, block reference
- Dimensions: linear, aligned, angular, radius, diameter
- Entity modification: move, copy, rotate, scale, mirror, offset, delete, rectangular/polar array
- Layer management: create, delete, set current, modify, freeze/thaw, lock/unlock, hide/show, isolate
- Block operations: list, insert, explode, attributes, create from entities, find references
- Analysis: entity stats, region search, distance/area measurement, bounding box, select by layer/type
- View control: zoom extents/window, screenshot
- Transaction support: begin, commit, rollback
- System tools: status, variables, command execution, AutoLISP evaluation
- 5 prompt templates: floor plan, P&ID, electrical schematic, mechanical drawing, quick drawing
