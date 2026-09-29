#!/usr/bin/env python3
"""Generate the synchronous resources from the asynchronous ones.

The async resources in ``py24so/resources/_async`` are the source of truth. This
script rewrites them into ``py24so/resources/_sync`` so both APIs stay identical.

Usage:
    python scripts/unasync.py          # regenerate
    python scripts/unasync.py --check  # exit 1 if the sync code is out of date
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "py24so" / "resources" / "_async"
TARGET = ROOT / "py24so" / "resources" / "_sync"

HEADER = "# AUTO-GENERATED from py24so/resources/_async by scripts/unasync.py. DO NOT EDIT.\n\n"

SUBSTITUTIONS = [
    (re.compile(r"\basync def "), "def "),
    (re.compile(r"\basync for "), "for "),
    (re.compile(r"\basync with "), "with "),
    (re.compile(r"\bawait "), ""),
    (re.compile(r"\b__aenter__\b"), "__enter__"),
    (re.compile(r"\b__aexit__\b"), "__exit__"),
    (re.compile(r"\b__aiter__\b"), "__iter__"),
    (re.compile(r"\bresources\._async\b"), "resources._sync"),
    # AsyncCustomers -> Customers, AsyncAPIClient -> APIClient, AsyncIterator -> Iterator
    (re.compile(r"\bAsync(?=[A-Z])"), ""),
    (re.compile(r"\basynchronously\b"), "synchronously"),
]


def unasync_source(source: str) -> str:
    for pattern, replacement in SUBSTITUTIONS:
        source = pattern.sub(replacement, source)
    return HEADER + source


def _format(files: Dict[Path, str]) -> Dict[Path, str]:
    """Run black and isort on the generated code so it passes the format check."""
    formatted = {}
    for path, text in files.items():
        for cmd in (
            [sys.executable, "-m", "isort", "--settings-path", str(ROOT), "-"],
            [
                sys.executable,
                "-m",
                "black",
                "--quiet",
                "--config",
                str(ROOT / "pyproject.toml"),
                "-",
            ],
        ):
            text = subprocess.run(
                cmd, input=text, capture_output=True, text=True, check=True, cwd=ROOT
            ).stdout
        formatted[path] = text
    return formatted


def generate() -> Dict[Path, str]:
    files = {
        TARGET / src.name: unasync_source(src.read_text(encoding="utf-8"))
        for src in sorted(SOURCE.glob("*.py"))
    }
    return _format(files)


def main() -> int:
    check = "--check" in sys.argv[1:]
    files = generate()
    stale = sorted(
        {p for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text}
        | {p for p in TARGET.glob("*.py") if p not in files}
    )
    if check:
        for path in stale:
            print(f"out of date: {path.relative_to(ROOT)}")
        if stale:
            print("Run: python scripts/unasync.py")
        return 1 if stale else 0

    TARGET.mkdir(parents=True, exist_ok=True)
    for path in TARGET.glob("*.py"):
        if path not in files:
            path.unlink()
    for path, text in files.items():
        path.write_text(text, encoding="utf-8")
    print(f"generated {len(files)} files in {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
