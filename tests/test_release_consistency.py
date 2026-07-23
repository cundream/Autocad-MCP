"""Release-consistency gates (v1.4.0 Faz 0).

Locks the version string, the README release snapshot, the server.py section
headers, and the Dockerfile file selection to the actual state of the tree so
none of them can drift again:

- pyproject version == CHANGELOG top release == README snapshot major.minor
- version.py fallback parser returns the pyproject version
- README snapshot tool/resource/prompt counts == live @mcp.* decorator counts
- every ``SECTION n: ... (N tools)`` header matches the decorators below it
- every wheel ``only-include`` entry is COPY'd into the Docker image
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def _pyproject_version() -> str:
    return str(_pyproject()["project"]["version"])


def _server_source() -> str:
    return (ROOT / "server.py").read_text(encoding="utf-8")


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def test_pyproject_version_is_semver() -> None:
    assert SEMVER_RE.match(_pyproject_version()), (
        f"pyproject version {_pyproject_version()!r} is not MAJOR.MINOR.PATCH"
    )


def test_version_py_fallback_matches_pyproject(monkeypatch: pytest.MonkeyPatch) -> None:
    """The pyproject fallback in version.py must resolve the same version.

    The installed-metadata short circuit is forced to miss so the test checks
    our parser (the code path a source checkout without an install uses).
    """
    import version as version_module

    def _raise(_name: str) -> str:
        raise version_module.PackageNotFoundError

    monkeypatch.setattr(version_module, "version", _raise)
    assert version_module.package_version() == _pyproject_version()


def test_changelog_top_release_matches_pyproject() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, flags=re.MULTILINE)
    assert match, "CHANGELOG.md has no '## [X.Y.Z]' release heading"
    assert match.group(1) == _pyproject_version(), (
        f"CHANGELOG top release {match.group(1)} != pyproject {_pyproject_version()}"
    )


def _readme_snapshot() -> tuple[str, int, int, int]:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # The snapshot may wrap across blockquote lines; join continuations first.
    flat = re.sub(r"\n>\s*", " ", readme)
    match = re.search(
        r"\*\*v(\d+\.\d+) release snapshot:\*\*\s*(\d+) tools\D+?(\d+) resources"
        r"\D+?(\d+) prompt templates",
        flat,
    )
    assert match, "README.md release-snapshot line not found or malformed"
    return match.group(1), int(match.group(2)), int(match.group(3)), int(match.group(4))


def test_readme_snapshot_matches_pyproject_minor() -> None:
    snapshot_minor, _, _, _ = _readme_snapshot()
    expected = ".".join(_pyproject_version().split(".")[:2])
    assert snapshot_minor == expected, (
        f"README snapshot v{snapshot_minor} != pyproject major.minor v{expected}"
    )


def test_readme_snapshot_counts_match_registrations() -> None:
    src = _server_source()
    tools = len(re.findall(r"@mcp\.tool\(", src))
    resources = len(re.findall(r"@mcp\.resource\(", src))
    prompts = len(re.findall(r"@mcp\.prompt\(", src))
    _, readme_tools, readme_resources, readme_prompts = _readme_snapshot()
    assert (readme_tools, readme_resources, readme_prompts) == (tools, resources, prompts), (
        f"README snapshot says {readme_tools}/{readme_resources}/{readme_prompts} "
        f"(tools/resources/prompts) but server.py registers {tools}/{resources}/{prompts}"
    )


def test_section_header_counts_match_decorators() -> None:
    src = _server_source()
    headers = [
        (m.start(), m.group(1), m.group(2))
        for m in re.finditer(r"#[^\n]*SECTION ([\w]+):[^\n]*?\((\d+) tools?\)", src)
    ]
    assert headers, "no counted SECTION headers found in server.py"
    # Segment boundaries: every SECTION header (counted or not) ends a segment.
    boundaries = sorted(m.start() for m in re.finditer(r"#[^\n]*SECTION [\w]+:", src))
    boundaries.append(len(src))
    mismatches: list[str] = []
    for start, section_id, declared in headers:
        end = min(b for b in boundaries if b > start)
        actual = len(re.findall(r"@mcp\.tool\(", src[start:end]))
        if actual != int(declared):
            mismatches.append(f"SECTION {section_id}: header says {declared}, actual {actual}")
    assert not mismatches, "; ".join(mismatches)


def test_server_json_versions_match_pyproject() -> None:
    """MCP registry manifest must ship the same version as the package."""
    import json

    manifest = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    expected = _pyproject_version()
    assert manifest["version"] == expected, (
        f"server.json version {manifest['version']} != pyproject {expected}"
    )
    for package in manifest["packages"]:
        assert package["version"] == expected, (
            f"server.json package {package['identifier']} version "
            f"{package['version']} != pyproject {expected}"
        )
        if package["registryType"] == "pypi":
            assert package["identifier"] == _pyproject()["project"]["name"]


def test_readme_contains_mcp_name_marker() -> None:
    """PyPI ownership validation for the MCP registry needs this marker in the
    README (which ships to PyPI as the long description)."""
    import json

    manifest = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"mcp-name: {manifest['name']}" in readme


def test_dockerfile_copies_every_wheel_include() -> None:
    """The Docker image must contain everything the wheel ships (GH bug: the
    image previously missed engineering/ and version.py)."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    copy_lines = "\n".join(
        line for line in dockerfile.splitlines() if line.strip().upper().startswith("COPY")
    )
    includes = _pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"]["only-include"]
    missing = [name for name in includes if name not in copy_lines]
    assert not missing, f"Dockerfile COPY misses wheel-shipped paths: {missing}"
