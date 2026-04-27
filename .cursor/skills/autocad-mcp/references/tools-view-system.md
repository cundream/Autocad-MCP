# View, Transaction & System Tools (14)

## View & Screenshot (5)

### view_zoom_extents
Zoom to show all entities. No parameters. **COM only** (no-op in ezdxf).

### view_zoom_window
Zoom to a specific rectangular area. **COM only**.

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | Window corner 1 |
| `x2, y2` | `float` | Window corner 2 |

### view_screenshot
Capture drawing as image. Returns base64-encoded image.

- **COM**: Win32 window capture (requires Pillow)
- **ezdxf**: matplotlib render (requires matplotlib)

### view_zoom_and_screenshot
Combined zoom + screenshot in one call.

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float \| null` | Optional zoom window corner 1 |
| `x2, y2` | `float \| null` | Optional zoom window corner 2 |

If coordinates omitted, captures full extents.

### view_set_view
Set named view. Parameters depend on backend.

---

## Transactions (3)

Use transactions to group operations with undo support.

```
transaction_begin()       # Save checkpoint
... make changes ...
transaction_commit()      # Accept changes
# or
transaction_rollback()    # Revert to checkpoint
```

### transaction_begin
Start a transaction. ezdxf saves full DXF snapshot; COM creates undo mark.

### transaction_commit
Accept all changes since `transaction_begin`.

### transaction_rollback
Revert all changes since `transaction_begin`. ezdxf restores snapshot; COM uses native undo.

---

## System (6)

### system_status
No parameters. Returns server status: `{backend, drawing_loaded, entity_count, uptime, ...}`.

### system_get_variable
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Variable name: `DIMSCALE`, `LTSCALE`, `INSUNITS`, `CLAYER`, `MEASUREMENT` |

### system_set_variable
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Variable name |
| `value` | `any` | New value |

### system_run_command
Execute raw AutoCAD command. **COM only**. Sanitized by `sanitize_command()`.

| Param | Type | Description |
|-------|------|-------------|
| `command` | `str` | Command string (e.g. `_ZOOM E`, `_REGEN`) |

Dangerous commands blocked unless `DANGEROUS_COMMANDS_ENABLED=true`.

### system_run_lisp
Evaluate AutoLISP expression. **COM only**. Sanitized by `sanitize_lisp()`.

| Param | Type | Description |
|-------|------|-------------|
| `expression` | `str` | LISP expression (e.g. `(command "ZOOM" "E")`) |

Dangerous functions blocked: `startapp`, `vl-file-delete`, `dos_*`.

### system_about
No parameters. Returns server capabilities, tool count, version, and feature list.
