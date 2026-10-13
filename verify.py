#!/usr/bin/env python3
"""Check the table against the current ISO 4217 register.

The register is read from `pycountry`, which packages it. Two things have to
hold, and either failing means the table is making a claim the register does
not support:

  * no code the table calls withdrawn may still be active,
  * every successor the table names must be active.

Run this when a currency changes, or on a schedule, rather than trusting the
table to stay true on its own.
"""

from __future__ import annotations

import sys

try:
    import pycountry
except ImportError:
    print("pycountry is needed to verify the table: pip install pycountry", file=sys.stderr)
    raise SystemExit(2)

from iso4217_audit.table import WITHDRAWN, chain


def main() -> int:
    active = {currency.alpha_3 for currency in pycountry.currencies}
    problems: list[str] = []

    for code, entry in sorted(WITHDRAWN.items()):
        if code in active:
            problems.append(f"{code} is listed as withdrawn but is still in the register")
        if entry.successor and entry.successor not in active and entry.successor not in WITHDRAWN:
            problems.append(
                f"{code} names {entry.successor} as its successor, which the register "
                f"has never heard of"
            )
        if entry.successor:
            # A chain of replacements has to end somewhere current, or the
            # table cannot tell anyone what to use instead.
            steps = chain(code)
            if not steps or steps[-1] not in active:
                problems.append(
                    f"{code} leads to {' -> '.join(steps) or 'nowhere'}, which is not active"
                )
        if entry.successor == code:
            problems.append(f"{code} names itself as its successor")
        if len(entry.effective) != 10 or entry.effective[4] != "-":
            problems.append(f"{code} has {entry.effective!r} where a YYYY-MM-DD date belongs")
        if not entry.note.endswith("."):
            problems.append(f"{code} has a note that is not a sentence")

    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        return 1

    successors = sum(1 for entry in WITHDRAWN.values() if entry.successor)
    print(
        f"ok: {len(WITHDRAWN)} withdrawn codes, {successors} with a successor, "
        f"checked against {len(active)} active codes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
