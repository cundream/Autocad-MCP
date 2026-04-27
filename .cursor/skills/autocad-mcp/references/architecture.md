# Architecture

## File Structure

```
server.py                    FastMCP 3.0 server — all tool/resource/prompt registrations
├── config.py                Settings class (pydantic-settings, env vars)
├── security.py              validate_path() + sanitize_command() + sanitize_lisp()
└── backends/
    ├── base.py              AutoCADBackend ABC + data models
    ├── ezdxf_backend.py     Headless DXF ops via ezdxf library
    └── com_backend.py       Live AutoCAD control via pywin32 COM
```

## Dual-Backend Strategy Pattern

`AutoCADBackend` (in `base.py`) is an abstract base class. Both backends implement the full interface. The server creates exactly one backend at startup via `_make_backend()`:

1. Check `AUTOCAD_MCP_BACKEND` env var
2. If `auto` or `com` on Windows: try COM → fall back to ezdxf
3. If non-Windows or `ezdxf`: use ezdxf

## Data Models

Defined in `base.py`:

- **EntityInfo**: `{handle, type, layer, color, linetype, visible, properties}`
- **LayerInfo**: `{name, color, linetype, lineweight, is_on, is_frozen, is_locked, is_current}`
- **BlockInfo**: `{name, origin, attribute_count, entity_count, is_xref, description}`
- **DrawingInfo**: `{name, full_path, saved, entity_count, layer_count, block_count, extents_min, extents_max, units, version, backend}`
- **CommandResult**: `{ok, payload, error}`

## Backend Differences

| Feature | ezdxf | COM |
|---------|-------|-----|
| Platform | Any | Windows only |
| AutoCAD needed | No | Yes (running) |
| View/zoom | No-op | Full control |
| Screenshots | matplotlib render | Win32 window capture |
| Commands/LISP | Not supported | Full support |
| Undo | DXF snapshot stack | Native AutoCAD undo |
| Threading | `asyncio.to_thread` via `_async()` | `ThreadPoolExecutor` (single thread, STA) |
| File formats | DXF only | DWG + DXF |

## FastMCP Server

The `mcp` object is configured with:
- **Lifespan**: `autocad_lifespan` — initializes backend, stores in `ctx.lifespan_context["backend"]`
- **Middleware**: ErrorHandling → AuditLog (custom timing) → Timing → Logging
- **`_backend(ctx)`**: Helper that retrieves backend from context, raises `ToolError` if unavailable

## Adding a New Tool

1. Add abstract method to `AutoCADBackend` in `backends/base.py`
2. Implement in `EzdxfBackend` — wrap sync calls with `_async(func)`
3. Implement in `ComBackend` — wrap COM calls with `self._com(func)`
4. Register in `server.py`: `@mcp.tool(...)` calling `_backend(ctx).method(...)`
5. Use `_dc(result)` to convert dataclass returns to dicts
6. Write tests in `tests/`
