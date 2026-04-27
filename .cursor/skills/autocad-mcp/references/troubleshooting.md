# Troubleshooting

## Common Errors

### "AutoCAD backend unavailable"
**Cause**: No drawing is loaded — backend needs an active drawing context.
**Fix**: Call `drawing_new()` or `drawing_open(path)` before any other operations.

### "Entity handle 'XXXX' not found"
**Cause**: Handle doesn't exist, was deleted, or drawing was reloaded.
**Fix**: Use `entity_list()` to get current valid handles. Handles are session-specific in ezdxf; persist by saving/reopening.

### "Layer 'X' not found"
**Cause**: Layer doesn't exist in the drawing.
**Fix**: `layer_list()` to see existing layers. `layer_create("X")` to create it.

### "Cannot delete layer '0'"
**Cause**: Layer "0" is the default layer and cannot be removed.
**Fix**: Move entities to another layer instead. Layer "0" always exists.

### "Path validation failed"
**Cause**: Path contains traversal (`..`) or is outside `ALLOWED_PATHS`.
**Fix**: Use absolute paths within configured allowed directories. Check `ALLOWED_PATHS` env var.

### "Command rejected by sanitizer"
**Cause**: `system_run_command` detected a dangerous pattern (ERASE, DELETE, etc.).
**Fix**: Use specific tools instead (e.g., `entity_delete` instead of `ERASE` command). Or set `DANGEROUS_COMMANDS_ENABLED=true` if needed.

### "LISP expression rejected"
**Cause**: `system_run_lisp` detected dangerous function (startapp, file ops).
**Fix**: Use MCP tools instead of LISP for file operations.

### "COM backend initialization failed"
**Cause**: AutoCAD not running, not installed, or COM registration issues.
**Fix**: Start AutoCAD, then retry. Or switch to ezdxf: `AUTOCAD_MCP_BACKEND=ezdxf`.

### "View operations are no-ops"
**Cause**: Using ezdxf backend — view/zoom commands only work with COM.
**Fix**: Switch to COM backend if live viewport control is needed. Screenshots still work via matplotlib in ezdxf.

### "Screenshot failed"
**Cause**: Missing dependency (Pillow for COM, matplotlib for ezdxf).
**Fix**: `pip install Pillow` (COM) or `pip install matplotlib` (ezdxf).

### "PDF export failed"
**Cause**: matplotlib not installed.
**Fix**: `pip install matplotlib` or `pip install -e ".[pdf]"`.

### "Transaction not active"
**Cause**: `transaction_commit/rollback` called without `transaction_begin`.
**Fix**: Always call `transaction_begin()` first.

### "Block 'X' not found"
**Cause**: Block definition doesn't exist.
**Fix**: `block_list()` to see available blocks. Create a block with `block_create_from_entities()`.

---

## Backend-Specific Issues

### ezdxf Backend
- **No DWG write support**: ezdxf reads DWG but can only write DXF. Use `drawing_export_dxf()`.
- **Undo stack memory**: Full DXF snapshots stored. `MAX_UNDO_STACK` env limits count (default: 50).
- **Text rendering**: Depends on system fonts. MathTex/complex formatting may not render in screenshots.

### COM Backend
- **STA threading**: All COM calls go through a single thread. Batch operations are sequential.
- **AutoCAD version**: Tested with AutoCAD 2020+. Older versions may have COM API differences.
- **Window capture**: Screenshots capture the AutoCAD window as-is. Minimize overlapping windows.

---

## Diagnostic Steps

1. `system_status()` — Check backend type, connection, drawing state
2. `system_about()` — See available tools and capabilities
3. `drawing_info()` — Verify drawing is loaded and get metadata
4. `analysis_entity_stats()` — Quick overview of drawing contents
5. Check logs: `LOG_LEVEL=DEBUG` for verbose output
