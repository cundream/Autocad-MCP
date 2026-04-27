"""Centralized configuration for AutoCAD MCP Pro."""

from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """Server configuration loaded from environment variables."""

    def __init__(self):
        self.backend: str = os.environ.get("AUTOCAD_MCP_BACKEND", "auto").lower().strip()
        self.log_level: str = os.environ.get("LOG_LEVEL", "INFO").upper().strip()

        raw_paths = os.environ.get("ALLOWED_PATHS", "").strip()
        self.allowed_paths: list[Path] = []
        if raw_paths:
            for p in raw_paths.split(","):
                p = p.strip()
                if p:
                    self.allowed_paths.append(Path(p).resolve())

        self.max_undo_stack: int = int(os.environ.get("MAX_UNDO_STACK", "5"))
        self.dangerous_commands_enabled: bool = (
            os.environ.get("DANGEROUS_COMMANDS_ENABLED", "false").lower().strip() == "true"
        )

        # Reject opening DXF files larger than this many bytes (default 50 MB).
        # Set to 0 to disable the check.
        self.max_dxf_bytes: int = int(os.environ.get("MAX_DXF_BYTES", str(50 * 1024 * 1024)))

        # Hard cap on list/select limit params to keep tool responses bounded.
        self.max_list_limit: int = int(os.environ.get("MAX_LIST_LIMIT", "5000"))

        # Per-call COM timeout. AutoCAD hangs (modal dialogs, long Regen) would
        # otherwise block the single-thread STA executor forever.
        self.com_call_timeout: float = float(os.environ.get("COM_CALL_TIMEOUT", "60"))

        # HTTP transport: refuse non-loopback bind unless explicitly opted in.
        self.allow_remote_http: bool = (
            os.environ.get("ALLOW_REMOTE_HTTP", "false").lower().strip() == "true"
        )
        self.mcp_auth_token: str = os.environ.get("MCP_AUTH_TOKEN", "").strip()


settings = Settings()
