"""Security utilities for AutoCAD MCP Pro.

Path traversal protection and command injection prevention.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from fastmcp.exceptions import ToolError

import config

log = logging.getLogger("autocad_mcp.security")

# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

_BLOCKED_PATH_PATTERNS = re.compile(
    r"(\.\.[\\/])"
    r"|(%2e%2e)"
    r"|(\\\\[?.]\\)"
    r"|(^\\\\)"
    r"|(\x00)",
    re.IGNORECASE,
)


def validate_path(path: str, *, allow_write: bool = False) -> Path:
    """Resolve and validate a file path against security rules.

    Raises ToolError if:
      - Path contains traversal sequences (..)
      - Path is outside ALLOWED_PATHS (when configured)
      - Path targets a system directory
    """
    if not path or not path.strip():
        raise ToolError("File path cannot be empty.")

    if _BLOCKED_PATH_PATTERNS.search(path):
        log.warning("Blocked path traversal attempt: %s", path)
        raise ToolError(
            f"Path rejected: suspicious traversal pattern detected in '{path}'. "
            "Use absolute paths without '..' components."
        )

    resolved = Path(path).resolve()

    _SYSTEM_DIRS = [
        Path("C:/Windows").resolve(),
        Path("C:/Program Files").resolve(),
        Path("C:/Program Files (x86)").resolve(),
        Path("/etc").resolve(),
        Path("/usr").resolve(),
        Path("/bin").resolve(),
        Path("/sbin").resolve(),
        Path("/boot").resolve(),
        Path("/sys").resolve(),
        Path("/proc").resolve(),
    ]
    for sys_dir in _SYSTEM_DIRS:
        try:
            if resolved.is_relative_to(sys_dir):
                log.warning("Blocked system directory access: %s", resolved)
                raise ToolError(
                    f"Path rejected: '{resolved}' is inside a system directory. "
                    "File operations in system directories are not allowed."
                )
        except (ValueError, TypeError):
            pass

    if config.settings.allowed_paths:
        allowed = False
        for allowed_dir in config.settings.allowed_paths:
            try:
                if resolved.is_relative_to(allowed_dir):
                    allowed = True
                    break
            except (ValueError, TypeError):
                pass
        if not allowed:
            allowed_str = ", ".join(str(p) for p in config.settings.allowed_paths)
            log.warning("Path outside allowed directories: %s", resolved)
            raise ToolError(
                f"Path rejected: '{resolved}' is not inside any allowed directory. "
                f"Allowed directories: {allowed_str}. "
                "Set ALLOWED_PATHS environment variable to configure."
            )

    if allow_write:
        parent = resolved.parent
        if not parent.exists():
            raise ToolError(
                f"Parent directory does not exist: '{parent}'. "
                "Create the directory first or use a valid path."
            )

    return resolved


# ---------------------------------------------------------------------------
# Command / LISP sanitization
# ---------------------------------------------------------------------------

_DANGEROUS_COMMANDS = [
    "ERASE", "_ERASE",
    "DELETE", "_DELETE",
    "PURGE", "_PURGE",
    "QUIT", "_QUIT",
    "CLOSE", "_CLOSE",
    "QSAVE", "_QSAVE",
    "SAVEAS", "_SAVEAS",
    "NEW", "_NEW",
    "OPEN", "_OPEN",
    "RECOVER", "_RECOVER",
    "WBLOCK", "_WBLOCK",
    "INSERT", "_INSERT",
    "XREF", "_XREF",
    "SHELL", "_SHELL",
    "SCRIPT", "_SCRIPT",
    "APPLOAD", "_APPLOAD",
    "NETLOAD", "_NETLOAD",
    "VBARUN", "_VBARUN",
    "VBALOAD", "_VBALOAD",
    "SECURITYOPTIONS", "_SECURITYOPTIONS",
]

_DANGEROUS_COMMAND_PATTERNS = re.compile(
    r"\b("
    + "|".join(re.escape(cmd) for cmd in _DANGEROUS_COMMANDS)
    + r")\b",
    re.IGNORECASE,
)

# Dangerous LISP symbols. We match these as **bare tokens anywhere** in the
# expression — not only when they appear right after `(` — because aliasing
# tricks like `(setq f command)(f "ERASE")` reference the symbol as a value.
_DANGEROUS_LISP_PATTERNS = [
    # File and shell I/O
    r"startapp",
    r"dos_[\w-]*",
    r"vl-file-(?:delete|rename|copy|directory-p)",
    r"vl-mkdir",
    r"vl-directory-files",
    r"read-line",
    r"write-line",
    r"findfile",
    r"getfiled",
    # Command execution (every known channel)
    r"command(?:-s)?",
    r"vl-cmdf",
    # ActiveX/COM family — vla-*, vlax-*, vlr-*; covers vla-SendCommand etc.
    r"vla[xr]?-[\w-]+",
    # AutoCAD Express Tools — acet-sys-shell and friends
    r"acet-[\w-]+",
    # Code loading
    r"vl-acad-(?:de|un)fun",
    r"(?:auto)?load",
    r"arxload",
    # Indirection vectors that bypass head-only matching
    r"eval",
    r"apply",
    r"funcall",
    r"function",
    r"\(\s*quote\s+command\b",
    # Custom command invocation prefix `(c:my-cmd)`
    r"c:[\w-]+",
    # Error handler hijack
    r"\*push-error-using-command\*",
    r"\*push-error-using-stack\*",
]

_DANGEROUS_LISP_PATTERN = re.compile(
    r"(?:(?<![\w-])|^)(?:" + "|".join(_DANGEROUS_LISP_PATTERNS) + r")(?![\w-])",
    re.IGNORECASE,
)


def sanitize_command(command: str) -> str:
    """Validate an AutoCAD command string for safety.

    Raises ToolError if a dangerous command pattern is detected
    (unless DANGEROUS_COMMANDS_ENABLED is true).
    """
    if not command or not command.strip():
        raise ToolError("Command string cannot be empty.")

    if config.settings.dangerous_commands_enabled:
        log.info("Dangerous commands enabled — bypassing sanitization for: %s", command[:80])
        return command

    if _DANGEROUS_COMMAND_PATTERNS.search(command):
        log.warning("Blocked dangerous command: %s", command[:120])
        raise ToolError(
            f"Command rejected: '{command[:80]}' contains a restricted command. "
            "Restricted commands include ERASE, DELETE, PURGE, QUIT, SHELL, SCRIPT, etc. "
            "Set DANGEROUS_COMMANDS_ENABLED=true to allow all commands."
        )

    return command


def sanitize_lisp(expression: str) -> str:
    """Validate an AutoLISP expression for safety.

    Raises ToolError if a dangerous LISP function is detected
    (unless DANGEROUS_COMMANDS_ENABLED is true).
    """
    if not expression or not expression.strip():
        raise ToolError("LISP expression cannot be empty.")

    if config.settings.dangerous_commands_enabled:
        log.info("Dangerous commands enabled — bypassing LISP sanitization for: %s", expression[:80])
        return expression

    if _DANGEROUS_LISP_PATTERN.search(expression):
        log.warning("Blocked dangerous LISP expression: %s", expression[:120])
        raise ToolError(
            "LISP expression rejected: contains a restricted function. "
            "Restricted functions include startapp, command, load, eval, file I/O, etc. "
            "Set DANGEROUS_COMMANDS_ENABLED=true to allow all LISP expressions."
        )

    return expression
