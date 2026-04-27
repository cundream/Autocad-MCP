"""Check AutoCAD MCP Pro setup and dependencies."""

import importlib
import os
import sys


def check(name: str, condition: bool, fix: str = ""):
    status = "OK" if condition else "MISSING"
    symbol = "[+]" if condition else "[-]"
    line = f"  {symbol} {name}: {status}"
    if not condition and fix:
        line += f"  ->  {fix}"
    print(line)
    return condition


def main():
    print("AutoCAD MCP Pro — Setup Check\n")
    ok_count = 0
    total = 0

    print("Python:")
    total += 1
    v = sys.version_info
    ok_count += check(
        f"Python {v.major}.{v.minor}.{v.micro}",
        v >= (3, 11),
        "Requires Python 3.11+",
    )

    print("\nRequired packages:")
    for pkg, install in [
        ("fastmcp", "pip install fastmcp"),
        ("ezdxf", "pip install ezdxf"),
        ("pydantic", "pip install pydantic"),
    ]:
        total += 1
        try:
            importlib.import_module(pkg)
            ok_count += check(pkg, True)
        except ImportError:
            ok_count += check(pkg, False, install)

    print("\nOptional packages:")
    for pkg, install, purpose in [
        ("win32com", "pip install pywin32", "COM backend"),
        ("PIL", "pip install Pillow", "Screenshots (COM)"),
        ("matplotlib", "pip install matplotlib", "PDF export + screenshots (ezdxf)"),
    ]:
        total += 1
        try:
            importlib.import_module(pkg)
            ok_count += check(f"{pkg} ({purpose})", True)
        except ImportError:
            ok_count += check(f"{pkg} ({purpose})", False, install)

    print("\nEnvironment variables:")
    for var, default in [
        ("AUTOCAD_MCP_BACKEND", "auto"),
        ("ALLOWED_PATHS", "(empty = all paths allowed)"),
        ("MAX_UNDO_STACK", "50"),
        ("LOG_LEVEL", "INFO"),
        ("DANGEROUS_COMMANDS_ENABLED", "false"),
    ]:
        val = os.environ.get(var, "")
        total += 1
        ok_count += check(var, True, "")
        if val:
            print(f"        Current value: {val}")
        else:
            print(f"        Default: {default}")

    print(f"\nResult: {ok_count}/{total} checks passed")
    return 0 if ok_count >= 4 else 1


if __name__ == "__main__":
    sys.exit(main())
