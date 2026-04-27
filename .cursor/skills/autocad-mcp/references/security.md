# Security

## Path Validation

All file-path tools pass through `validate_path()` in `security.py`.

**How it works**:
- Resolves path via `Path.resolve()` (removes `..`, symlinks)
- Checks against `ALLOWED_PATHS` env var (comma-separated directories)
- If `ALLOWED_PATHS` is empty → all paths allowed (backward compat)
- Separate `allow_write` flag for read vs write operations

**Tools with path validation**:
- `drawing_open` (read)
- `drawing_save`, `drawing_save_as` (write)
- `drawing_export_dxf`, `drawing_export_pdf` (write)
- `drawing_new` with template (read)

**Blocked examples**:
- `../../../etc/passwd` → rejected (traversal)
- `C:\Windows\System32\...` → rejected if not in ALLOWED_PATHS
- Relative paths with `..` → always rejected

## Command Sanitization

`sanitize_command()` checks `system_run_command` input:

**Blocked patterns**: `ERASE`, `DELETE`, `PURGE`, `QUIT`, `CLOSE`, `_QUIT`, shell-related commands

**Override**: Set `DANGEROUS_COMMANDS_ENABLED=true` to bypass.

## LISP Sanitization

`sanitize_lisp()` checks `system_run_lisp` input:

**Blocked functions**: `startapp`, `vl-file-delete`, `vl-file-rename`, `dos_*` (file system access), `command` with dangerous args

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_PATHS` | (empty) | Comma-separated allowed directories. Empty = all allowed |
| `DANGEROUS_COMMANDS_ENABLED` | `false` | Allow blocked commands |
| `AUTOCAD_MCP_BACKEND` | `auto` | Backend selection |
| `MAX_UNDO_STACK` | `50` | Max undo snapshots (ezdxf) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Best Practices

- Always set `ALLOWED_PATHS` in production to restrict file access
- Never pass raw user input to `system_run_command` or `system_run_lisp`
- Use `transaction_begin/rollback` for destructive batch operations
- Review audit logs for suspicious tool calls (AuditMiddleware logs all calls)
