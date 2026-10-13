"""Find currency codes a codebase still uses after ISO 4217 withdrew them."""

from __future__ import annotations

import argparse
import os
import pathlib
import re
from typing import NamedTuple

from .table import WITHDRAWN, Withdrawal, describe

__version__ = "0.1.0"
__all__ = ["WITHDRAWN", "Withdrawal", "describe", "scan_text", "scan_path", "main"]

# A withdrawn code counts only as a standalone upper-case token. Requiring the
# boundaries keeps "ANG" out of "ANGLE" and "CHANGE", which is most of what
# separates a report worth reading from a wall of noise.
_TOKEN = re.compile(r"(?<![A-Za-z0-9_])([A-Z]{3})(?![A-Za-z0-9_])")

_SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "target", "dist", "build",
    "vendor", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache",
}


class Finding(NamedTuple):
    path: pathlib.Path
    line_number: int
    code: str
    line: str

    @property
    def withdrawal(self) -> Withdrawal:
        return WITHDRAWN[self.code]


def scan_text(text: str, path: pathlib.Path = pathlib.Path("-")) -> list[Finding]:
    """Every withdrawn code appearing as a standalone token in `text`."""
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for match in _TOKEN.finditer(line):
            code = match.group(1)
            if code in WITHDRAWN:
                findings.append(Finding(path, number, code, line.strip()))
    return findings


def scan_path(
    root: pathlib.Path,
    extensions: set[str] | None = None,
    max_bytes: int = 2_000_000,
) -> list[Finding]:
    findings: list[Finding] = []
    paths: list[pathlib.Path] = []
    if root.is_file():
        paths = [root]
    else:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            paths.extend(pathlib.Path(dirpath) / name for name in filenames)

    for path in sorted(paths):
        if extensions and path.suffix.lstrip(".") not in extensions:
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_text(text, path))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iso4217-audit",
        description="Find currency codes a codebase still uses after ISO 4217 withdrew them.",
    )
    parser.add_argument("paths", nargs="*", type=pathlib.Path, default=[pathlib.Path(".")])
    parser.add_argument(
        "--ext",
        default="",
        help="comma separated extensions to scan, without dots; default is every file",
    )
    parser.add_argument(
        "--ignore",
        default="",
        help="comma separated codes to accept, for a table that is deliberately historical",
    )
    parser.add_argument(
        "--since",
        default="",
        help="only report withdrawals that took effect on or after this date (YYYY-MM-DD)",
    )
    parser.add_argument("--list", action="store_true", help="print the table and exit")
    parser.add_argument("--quiet", action="store_true", help="only print the summary")
    parser.add_argument("--version", action="version", version=f"iso4217-audit {__version__}")
    args = parser.parse_args(argv)

    if args.list:
        for code in sorted(WITHDRAWN):
            print(describe(code))
        return 0

    ignored = {c.strip().upper() for c in args.ignore.split(",") if c.strip()}
    extensions = {e.strip().lstrip(".") for e in args.ext.split(",") if e.strip()}

    findings = [
        finding
        for path in args.paths
        for finding in scan_path(path, extensions or None)
        if finding.code not in ignored
        and (not args.since or finding.withdrawal.effective >= args.since)
    ]

    if not args.quiet:
        for finding in findings:
            print(f"{finding.path}:{finding.line_number}: {describe(finding.code)}")
            print(f"    {finding.line}")

    codes = sorted({f.code for f in findings})
    print(
        f"\n{len(findings)} occurrence(s) of {len(codes)} withdrawn code(s)"
        + (f": {', '.join(codes)}" if codes else "")
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
