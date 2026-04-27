# Drawing Management Tools (11)

## Contents
- [drawing_info](#drawing_info)
- [drawing_new](#drawing_new)
- [drawing_open](#drawing_open)
- [drawing_save](#drawing_save)
- [drawing_save_as](#drawing_save_as)
- [drawing_export_dxf](#drawing_export_dxf)
- [drawing_export_pdf](#drawing_export_pdf)
- [drawing_purge](#drawing_purge)
- [drawing_audit](#drawing_audit)
- [drawing_undo / drawing_redo](#drawing_undo--drawing_redo)

---

## drawing_info
Read-only. Returns comprehensive metadata for the current drawing.

**Returns**: `{name, full_path, saved, entity_count, layer_count, block_count, extents_min, extents_max, units, version, backend}`

---

## drawing_new
Create a new empty drawing, optionally from a template.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `template` | `str \| null` | No | Path to `.dwt` template file |

Path validation applied to template. Returns drawing info dict.

---

## drawing_open
Open an existing DWG or DXF file. Reports progress.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | `str` | Yes | Full path to `.dwg` or `.dxf` file |

Path validation: `allow_write=False`. Returns drawing info dict.

---

## drawing_save
Save current drawing. Uses current path if omitted.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | `str \| null` | No | Optional save path |

Path validation: `allow_write=True`.

---

## drawing_save_as
Save drawing to a new path.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | `str` | Yes | Full destination path with extension |

Path validation: `allow_write=True`.

---

## drawing_export_dxf
Export drawing as DXF file.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | `str` | Yes | Output `.dxf` file path |
| `version` | `str` | No | DXF version: `R2010`, `R2013`, `R2018` (default: `R2018`) |

---

## drawing_export_pdf
Export drawing as PDF. Requires `matplotlib`.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | `str` | Yes | Output `.pdf` file path |

---

## drawing_purge
Remove all unused objects (layers, blocks, linetypes, styles). No parameters.

---

## drawing_audit
Run integrity audit — detect and fix drawing errors. No parameters.

---

## drawing_undo / drawing_redo
Undo/redo last operation.

- **ezdxf**: Snapshot-based (restores full DXF state from `_undo_stack`)
- **COM**: Native AutoCAD undo/redo

**Note**: For multi-step undo protection, use `transaction_begin/rollback` instead.
