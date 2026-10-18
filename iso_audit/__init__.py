"""Find standard codes a codebase still uses after the standard withdrew them.

Two registers are covered, and they are deliberately kept apart. `ZAR` is the
South African rand and it is also the code ISO 3166 used for Zaire until 1997;
`GEL` is the Georgian lari and was the Gilbert and Ellice Islands. Scanning
for both at once would report every mention of those two currencies as a dead
country. Pick the register you mean.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Callable, NamedTuple

from . import country as _country
from .currency import WITHDRAWN, Withdrawal, chain, describe

__version__ = "0.2.0"
__all__ = [
    "WITHDRAWN", "Withdrawal", "describe", "chain",
    "Standard", "CURRENCY", "COUNTRY", "STANDARDS",
    "Finding", "scan_text", "scan_path", "check_codes", "main",
]

# A code counts only as a standalone upper-case token. Requiring the
# boundaries keeps "ANG" out of "ANGLE" and "CHANGE", which is most of what
# separates a report worth reading from a wall of noise.
_TOKEN = re.compile(r"(?<![A-Za-z0-9_])([A-Z]{3})(?![A-Za-z0-9_])")

_SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "target", "dist", "build",
    "vendor", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache",
}


class Standard(NamedTuple):
    """One register: what is withdrawn from it, and how to explain a code."""

    name: str
    register: str
    table: dict[str, object]  # scannable codes -> an entry with .effective
    describe: Callable[[str], str]
    short_codes: dict[str, str]  # two-letter code -> its three-letter form
    short_excluded: dict[str, str]  # two-letter codes the register still assigns


CURRENCY = Standard(
    name="currency",
    register="ISO 4217",
    table=dict(WITHDRAWN),
    describe=describe,
    short_codes={},
    short_excluded={},
)

COUNTRY = Standard(
    name="country",
    register="ISO 3166",
    table=dict(_country.reportable()),
    describe=_country.describe,
    short_codes=dict(_country.alpha2_table()),
    short_excluded=dict(_country.ALPHA2_STILL_ACTIVE),
)

STANDARDS = {s.name: s for s in (CURRENCY, COUNTRY)}


class Finding(NamedTuple):
    path: pathlib.Path
    line_number: int
    code: str
    line: str
    standard: Standard = CURRENCY

    @property
    def entry(self):
        return self.standard.table[self.code]

    @property
    def withdrawal(self) -> Withdrawal:
        """Kept for callers written against the currency-only version."""
        return WITHDRAWN[self.code]


def scan_text(
    text: str,
    path: pathlib.Path = pathlib.Path("-"),
    standard: Standard = CURRENCY,
) -> list[Finding]:
    """Every withdrawn code appearing as a standalone token in `text`."""
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for match in _TOKEN.finditer(line):
            code = match.group(1)
            if code in standard.table:
                findings.append(Finding(path, number, code, line.strip(), standard))
    return findings


def scan_path(
    root: pathlib.Path,
    extensions: set[str] | None = None,
    max_bytes: int = 2_000_000,
    standard: Standard = CURRENCY,
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
        findings.extend(scan_text(text, path, standard))
    return findings


def read_codes(text: str) -> list[str]:
    """Codes from a JSON array, or one per line.

    A list of country codes is the one place two-letter codes can be checked:
    in a file that holds nothing else, `SU` is the USSR rather than a variable.
    """
    stripped = text.strip()
    if stripped.startswith("{"):
        raise ValueError("expected a list of codes, not a JSON object")
    if stripped.startswith("["):
        loaded = json.loads(stripped)
        if not isinstance(loaded, list):
            raise ValueError("expected a JSON array of codes")
        values = loaded
    else:
        values = [line for line in stripped.splitlines()]
    codes = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"expected a string code, got {value!r}")
        token = value.strip().strip(",\"'").upper()
        if token:
            codes.append(token)
    return codes


def check_codes(codes: list[str], standard: Standard) -> list[tuple[str, str]]:
    """Withdrawn codes in an explicit list, as (code, explanation) pairs.

    Unlike scanning, this accepts the register's short codes too, because a
    list of codes carries no other kind of word.
    """
    out: list[tuple[str, str]] = []
    for code in codes:
        if code in standard.table:
            out.append((code, standard.describe(code)))
        elif code in standard.short_codes:
            # The alpha-3 a short code points at may itself be unreportable:
            # GE is the Gilbert and Ellice Islands, whose alpha-3 GEL is the
            # Georgian lari. In a list of country codes there is no ambiguity.
            out.append((code, standard.describe(standard.short_codes[code])))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iso-audit",
        description="Find standard codes a codebase still uses after the standard withdrew them.",
    )
    parser.add_argument("paths", nargs="*", type=pathlib.Path, default=[pathlib.Path(".")])
    parser.add_argument(
        "--standard",
        choices=sorted(STANDARDS),
        default="currency",
        help="which register to check; they are not combined, because a retired "
             "country code can be an active currency code (default: currency)",
    )
    parser.add_argument(
        "--codes",
        type=pathlib.Path,
        help="check an explicit list of codes in this file (or - for stdin) instead of "
             "scanning; this is the only mode that accepts two-letter country codes",
    )
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
    parser.add_argument("--version", action="version", version=f"iso-audit {__version__}")
    args = parser.parse_args(argv)

    standard = STANDARDS[args.standard]

    if args.list:
        for code in sorted(standard.table):
            print(standard.describe(code))
        for code, meaning in sorted(standard.short_excluded.items()):
            print(f"{code} is not reported: the register assigns it to {meaning}.")
        return 0

    ignored = {c.strip().upper() for c in args.ignore.split(",") if c.strip()}

    if args.codes:
        text = sys.stdin.read() if str(args.codes) == "-" else args.codes.read_text()
        try:
            codes = read_codes(text)
        except (ValueError, json.JSONDecodeError) as error:
            print(f"iso-audit: {args.codes}: {error}", file=sys.stderr)
            return 2
        hits = [(c, why) for c, why in check_codes(codes, standard) if c not in ignored]
        if not args.quiet:
            for code, why in hits:
                print(why)
        print(f"\n{len(codes)} code(s) checked, {len(hits)} withdrawn")
        return 1 if hits else 0

    extensions = {e.strip().lstrip(".") for e in args.ext.split(",") if e.strip()}
    findings = [
        finding
        for path in args.paths
        for finding in scan_path(path, extensions or None, standard=standard)
        if finding.code not in ignored
        and (not args.since or finding.entry.effective >= args.since)
    ]

    if not args.quiet:
        for finding in findings:
            print(f"{finding.path}:{finding.line_number}: {standard.describe(finding.code)}")
            print(f"    {finding.line}")

    codes = sorted({f.code for f in findings})
    print(
        f"\n{len(findings)} occurrence(s) of {len(codes)} withdrawn "
        f"{standard.name} code(s)" + (f": {', '.join(codes)}" if codes else "")
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
