"""Security tests for path validation and command sanitization."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from security import sanitize_command, sanitize_lisp, validate_path

# ---------------------------------------------------------------------------
# Path validation tests
# ---------------------------------------------------------------------------


class TestValidatePath:
    """Tests for validate_path function."""

    def test_valid_absolute_path(self, tmp_path):
        """Valid absolute path should resolve correctly."""
        test_file = tmp_path / "drawing.dxf"
        test_file.touch()
        result = validate_path(str(test_file), allow_write=False)
        assert result.exists()

    def test_empty_path_rejected(self):
        """Empty path should raise ToolError."""
        with pytest.raises(ToolError, match="cannot be empty"):
            validate_path("")

    def test_whitespace_path_rejected(self):
        """Whitespace-only path should raise ToolError."""
        with pytest.raises(ToolError, match="cannot be empty"):
            validate_path("   ")

    def test_traversal_dot_dot_slash(self):
        """Path with ../ should be rejected."""
        with pytest.raises(ToolError, match="traversal"):
            validate_path("../../../etc/passwd")

    def test_traversal_dot_dot_backslash(self):
        """Path with ..\\ should be rejected."""
        with pytest.raises(ToolError, match="traversal"):
            validate_path("..\\..\\Windows\\System32\\cmd.exe")

    def test_traversal_encoded(self):
        """URL-encoded traversal should be rejected."""
        with pytest.raises(ToolError, match="traversal"):
            validate_path("%2e%2e/secret")

    def test_null_byte(self):
        """Null byte in path should be rejected."""
        with pytest.raises(ToolError, match="traversal"):
            validate_path("file\x00.dxf")

    def test_write_requires_existing_parent(self, tmp_path):
        """Write mode should check parent directory exists."""
        nonexistent = tmp_path / "nonexistent_dir" / "file.dxf"
        with pytest.raises(ToolError, match="Parent directory"):
            validate_path(str(nonexistent), allow_write=True)

    def test_write_with_valid_parent(self, tmp_path):
        """Write mode should pass when parent exists."""
        target = tmp_path / "output.dxf"
        result = validate_path(str(target), allow_write=True)
        assert result.parent.exists()

    def test_allowed_paths_enforcement(self, tmp_path, monkeypatch):
        """When ALLOWED_PATHS is set, paths outside should be rejected."""
        from config import Settings

        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        monkeypatch.setenv("ALLOWED_PATHS", str(allowed_dir))

        import config
        config.settings = Settings()

        blocked = tmp_path / "blocked" / "file.dxf"
        blocked.parent.mkdir(exist_ok=True)
        blocked.touch()
        with pytest.raises(ToolError, match="not inside any allowed"):
            validate_path(str(blocked))

        config.settings = Settings.__new__(Settings)
        config.settings.allowed_paths = []
        config.settings.dangerous_commands_enabled = False
        monkeypatch.delenv("ALLOWED_PATHS", raising=False)
        config.settings = Settings()

    def test_allowed_paths_permits_inside(self, tmp_path, monkeypatch):
        """When ALLOWED_PATHS is set, paths inside should be allowed."""
        from config import Settings

        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        test_file = allowed_dir / "drawing.dxf"
        test_file.touch()
        monkeypatch.setenv("ALLOWED_PATHS", str(allowed_dir))

        import config
        config.settings = Settings()

        result = validate_path(str(test_file))
        assert result.exists()

        monkeypatch.delenv("ALLOWED_PATHS", raising=False)
        config.settings = Settings()


# ---------------------------------------------------------------------------
# Command sanitization tests
# ---------------------------------------------------------------------------


class TestSanitizeCommand:
    """Tests for sanitize_command function."""

    def test_safe_command_passes(self):
        """Safe commands should pass through."""
        assert sanitize_command("_ZOOM E") == "_ZOOM E"

    def test_safe_regen_command(self):
        """REGEN command should pass."""
        assert sanitize_command("_REGEN") == "_REGEN"

    def test_empty_command_rejected(self):
        """Empty command should raise ToolError."""
        with pytest.raises(ToolError, match="cannot be empty"):
            sanitize_command("")

    def test_erase_command_blocked(self):
        """ERASE command should be blocked."""
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("ERASE ALL")

    def test_delete_command_blocked(self):
        """DELETE command should be blocked."""
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("DELETE")

    def test_shell_command_blocked(self):
        """SHELL command should be blocked."""
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("SHELL")

    def test_quit_command_blocked(self):
        """QUIT command should be blocked."""
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("QUIT")

    def test_script_command_blocked(self):
        """SCRIPT command should be blocked."""
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("SCRIPT malicious.scr")

    def test_dangerous_enabled_bypass(self, monkeypatch):
        """When DANGEROUS_COMMANDS_ENABLED=true, all commands pass."""
        from config import Settings

        monkeypatch.setenv("DANGEROUS_COMMANDS_ENABLED", "true")

        import config
        config.settings = Settings()

        result = sanitize_command("ERASE ALL")
        assert result == "ERASE ALL"

        monkeypatch.delenv("DANGEROUS_COMMANDS_ENABLED", raising=False)
        config.settings = Settings()


# ---------------------------------------------------------------------------
# LISP sanitization tests
# ---------------------------------------------------------------------------


class TestSanitizeLisp:
    """Tests for sanitize_lisp function."""

    def test_safe_lisp_passes(self):
        """Safe LISP expressions should pass."""
        assert sanitize_lisp('(setvar "DIMSCALE" 1.0)') == '(setvar "DIMSCALE" 1.0)'

    def test_safe_arithmetic(self):
        """Simple arithmetic LISP should pass."""
        assert sanitize_lisp("(+ 1 2 3)") == "(+ 1 2 3)"

    def test_empty_expression_rejected(self):
        """Empty expression should raise ToolError."""
        with pytest.raises(ToolError, match="cannot be empty"):
            sanitize_lisp("")

    def test_startapp_blocked(self):
        """startapp should be blocked (arbitrary program execution)."""
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(startapp "cmd")')

    def test_command_function_blocked(self):
        """(command ...) should be blocked."""
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(command "ERASE" "ALL" "")')

    def test_file_delete_blocked(self):
        """vl-file-delete should be blocked."""
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(vl-file-delete "C:/important.dwg")')

    def test_load_blocked(self):
        """(load ...) should be blocked."""
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(load "malicious.lsp")')

    def test_eval_blocked(self):
        """(eval ...) should be blocked."""
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp("(eval (read user-input))")

    def test_dangerous_enabled_bypass(self, monkeypatch):
        """When DANGEROUS_COMMANDS_ENABLED=true, all LISP passes."""
        from config import Settings

        monkeypatch.setenv("DANGEROUS_COMMANDS_ENABLED", "true")

        import config
        config.settings = Settings()

        result = sanitize_lisp('(startapp "cmd")')
        assert result == '(startapp "cmd")'

        monkeypatch.delenv("DANGEROUS_COMMANDS_ENABLED", raising=False)
        config.settings = Settings()


class TestSanitizerBypassVectors:
    """R8 — adversarial coverage: the deny-list must hold against common evasion
    tricks. Each asserts the guard REJECTS the payload (defensive verification),
    plus that legitimate input is NOT over-blocked."""

    def test_command_newline_injected_second_command(self):
        # A safe head command with a dangerous one smuggled after a newline.
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("_ZOOM E\n_ERASE")

    def test_command_case_insensitive(self):
        with pytest.raises(ToolError, match="restricted command"):
            sanitize_command("eRaSe all")

    def test_command_legitimate_not_overblocked(self):
        assert sanitize_command("_LINE 0,0 10,10") == "_LINE 0,0 10,10"

    def test_lisp_symbol_aliasing_blocked(self):
        # (setq f command) references `command` as a value to dodge head-only
        # matching — the bare-token scan must still catch it.
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp("(setq f command)(f)")

    def test_lisp_activex_family_blocked(self):
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(vlax-invoke obj "SendCommand" "x")')

    def test_lisp_express_tools_shell_blocked(self):
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(acet-sys-shell "cmd")')

    def test_lisp_custom_command_invocation_blocked(self):
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp("(c:mycmd)")

    def test_lisp_dangerous_token_inside_wrapper_blocked(self):
        with pytest.raises(ToolError, match="restricted function"):
            sanitize_lisp('(startapp (strcat "c" "md"))')

    def test_lisp_legitimate_not_overblocked(self):
        assert sanitize_lisp("(setq x (* 2 3))") == "(setq x (* 2 3))"
