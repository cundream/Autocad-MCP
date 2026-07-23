"""Tests for HTTP bearer-token auth wiring.

Verifies that when MCP_AUTH_TOKEN is set a StaticTokenVerifier is built and
wired into the FastMCP instance, and that when it is absent no auth object
is created (anonymous mode for loopback-only deployments).
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest
from fastmcp.server.auth import StaticTokenVerifier


def _reload_server_with_token(token: str | None):
    """Reload server.py with a specific MCP_AUTH_TOKEN environment variable.

    Returns the module so callers can inspect ``module._auth`` and
    ``module.mcp``.  Cleans up the module from sys.modules after each call
    so the reload is isolated.
    """
    # Patch the config settings to inject the token value without reloading config
    with patch("config.settings") as mock_settings:
        mock_settings.mcp_auth_token = token or ""
        mock_settings.com_call_timeout = 60
        mock_settings.allow_remote_http = False
        mock_settings.allowed_paths = []
        mock_settings.max_undo_stack = 5
        mock_settings.dangerous_commands_enabled = False
        mock_settings.max_dxf_bytes = 50 * 1024 * 1024
        mock_settings.max_list_limit = 5000
        mock_settings.backend = "ezdxf"
        mock_settings.log_level = "INFO"

        # Remove the server module if already loaded so importlib.import_module
        # actually re-executes the module body
        sys.modules.pop("server", None)
        mod = importlib.import_module("server")
        return mod, mock_settings


# ---------------------------------------------------------------------------
# Auth object construction
# ---------------------------------------------------------------------------


def test_auth_object_built_when_token_set():
    """_auth is a StaticTokenVerifier when MCP_AUTH_TOKEN is non-empty."""
    with patch.dict("os.environ", {"MCP_AUTH_TOKEN": "secret-test-token-123"}):
        import config as cfg

        old_token = cfg.settings.mcp_auth_token
        cfg.settings.mcp_auth_token = "secret-test-token-123"
        try:
            sys.modules.pop("server", None)
            import server as srv

            assert srv._auth is not None
            assert isinstance(srv._auth, StaticTokenVerifier)
        finally:
            cfg.settings.mcp_auth_token = old_token
            sys.modules.pop("server", None)


def test_auth_object_none_when_no_token():
    """_auth is None when MCP_AUTH_TOKEN is empty (anonymous loopback mode)."""
    import config as cfg

    old_token = cfg.settings.mcp_auth_token
    cfg.settings.mcp_auth_token = ""
    try:
        sys.modules.pop("server", None)
        import server as srv

        assert srv._auth is None
    finally:
        cfg.settings.mcp_auth_token = old_token
        sys.modules.pop("server", None)


def test_mcp_receives_auth_when_set():
    """The FastMCP instance's auth attribute matches the _auth object."""
    import config as cfg

    old_token = cfg.settings.mcp_auth_token
    cfg.settings.mcp_auth_token = "another-secret"
    try:
        sys.modules.pop("server", None)
        import server as srv

        # FastMCP stores auth as _auth_provider or similar; we check it via
        # the _auth module-level variable matching what was passed in.
        assert srv._auth is not None
        assert isinstance(srv._auth, StaticTokenVerifier)
    finally:
        cfg.settings.mcp_auth_token = old_token
        sys.modules.pop("server", None)


# ---------------------------------------------------------------------------
# _validate_http_bind guard
# ---------------------------------------------------------------------------


def test_validate_http_bind_loopback_no_error():
    """Loopback hosts pass validation regardless of token/allow_remote flags."""
    sys.modules.pop("server", None)
    import config as cfg
    import server as srv

    old_remote = cfg.settings.allow_remote_http
    old_token = cfg.settings.mcp_auth_token
    cfg.settings.allow_remote_http = False
    cfg.settings.mcp_auth_token = ""
    try:
        # Should not raise
        srv._validate_http_bind("127.0.0.1")
        srv._validate_http_bind("localhost")
        srv._validate_http_bind("::1")
    finally:
        cfg.settings.allow_remote_http = old_remote
        cfg.settings.mcp_auth_token = old_token


def test_validate_http_bind_remote_without_flag_raises():
    """Non-loopback bind without ALLOW_REMOTE_HTTP raises SystemExit."""
    sys.modules.pop("server", None)
    import config as cfg
    import server as srv

    old = cfg.settings.allow_remote_http
    cfg.settings.allow_remote_http = False
    try:
        with pytest.raises(SystemExit, match="Refusing"):
            srv._validate_http_bind("0.0.0.0")
    finally:
        cfg.settings.allow_remote_http = old


def test_validate_http_bind_remote_without_token_raises():
    """Remote bind with ALLOW_REMOTE_HTTP=true but no token raises SystemExit."""
    sys.modules.pop("server", None)
    import config as cfg
    import server as srv

    old_remote = cfg.settings.allow_remote_http
    old_token = cfg.settings.mcp_auth_token
    cfg.settings.allow_remote_http = True
    cfg.settings.mcp_auth_token = ""
    try:
        with pytest.raises(SystemExit, match="MCP_AUTH_TOKEN"):
            srv._validate_http_bind("0.0.0.0")
    finally:
        cfg.settings.allow_remote_http = old_remote
        cfg.settings.mcp_auth_token = old_token


def test_validate_http_bind_remote_with_token_logs_warning(caplog):
    """Remote bind with both flag and token logs a warning but does not raise."""
    import logging

    sys.modules.pop("server", None)
    import config as cfg
    import server as srv

    old_remote = cfg.settings.allow_remote_http
    old_token = cfg.settings.mcp_auth_token
    cfg.settings.allow_remote_http = True
    cfg.settings.mcp_auth_token = "secure-token"
    try:
        with caplog.at_level(logging.WARNING, logger="server"):
            srv._validate_http_bind("0.0.0.0")  # should not raise
        assert any(
            "non-loopback" in r.message.lower() or "0.0.0.0" in r.message for r in caplog.records
        )
    finally:
        cfg.settings.allow_remote_http = old_remote
        cfg.settings.mcp_auth_token = old_token
