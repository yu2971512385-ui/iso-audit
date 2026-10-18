#!/usr/bin/env python3
"""Check both tables against the registers they claim to follow.

The registers are read from `pycountry`, which packages them. For each table,
two things have to hold, and either failing means the table is making a claim
the register does not support:

  * no code the table calls withdrawn may still be active,
  * following the successors has to arrive at codes that are.

The country table carries a third obligation. Its entries have to match ISO
3166-3 exactly -- no inventing a retirement, no missing one -- because its
whole value is being the list a maintainer does not have to assemble.

Run this when a currency or a country changes, or on a schedule, rather than
trusting the tables to stay true on their own.
"""

from __future__ import annotations

import sys

try:
    import pycountry
except ImportError:
    print("pycountry is needed to verify the tables: pip install pycountry", file=sys.stderr)
    raise SystemExit(2)

from iso_audit import country
from iso_audit.currency import WITHDRAWN, chain


def check_date(code: str, effective: str, problems: list[str], exact: bool) -> None:
    """A date is YYYY-MM-DD, or YYYY where that is all ISO published."""
    if exact:
        if len(effective) != 10 or effective[4] != "-":
            problems.append(f"{code} has {effective!r} where a YYYY-MM-DD date belongs")
    elif not (len(effective) == 4 or (len(effective) == 10 and effective[4] == "-")):
        problems.append(f"{code} has {effective!r} where a date belongs")


def verify_currency() -> list[str]:
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
        check_date(code, entry.effective, problems, exact=True)
        if not entry.note.endswith("."):
            problems.append(f"{code} has a note that is not a sentence")

    if not problems:
        successors = sum(1 for entry in WITHDRAWN.values() if entry.successor)
        print(
            f"ok: ISO 4217, {len(WITHDRAWN)} withdrawn codes, {successors} with a "
            f"successor, checked against {len(active)} active codes"
        )
    return problems


def verify_country() -> list[str]:
    active_2 = {c.alpha_2 for c in pycountry.countries}
    active_3 = {c.alpha_3 for c in pycountry.countries}
    problems: list[str] = []

    # Every ISO 3166-3 entry has to be in the table, and every table entry that
    # claims to be a 3166-3 entry has to be one. A code change inside 3166-1,
    # such as ROM to ROU, has alpha_4 None and is exempt.
    register = {c.alpha_3: c for c in pycountry.historic_countries}
    claimed = {code: e for code, e in country.RETIRED.items() if e.alpha_4}
    for code in sorted(set(register) - set(claimed)):
        problems.append(f"{code} is in ISO 3166-3 and missing from the table")
    for code in sorted(set(claimed) - set(register)):
        problems.append(f"{code} claims an ISO 3166-3 entry the register does not have")
    for code in sorted(set(register) & set(claimed)):
        entry, official = claimed[code], register[code]
        if entry.alpha_4 != official.alpha_4:
            problems.append(
                f"{code} cites {entry.alpha_4}, but the register says {official.alpha_4}"
            )
        if entry.alpha_2 != getattr(official, "alpha_2", None):
            problems.append(
                f"{code} says its alpha-2 was {entry.alpha_2}, but the register says "
                f"{getattr(official, 'alpha_2', None)}"
            )

    for code, entry in sorted(country.RETIRED.items()):
        if code in active_3 and code not in country.STILL_ACTIVE_ALPHA3:
            problems.append(
                f"{code} is listed as retired, is still in the register, and is not "
                f"recorded as an alpha-3 that was reissued"
            )
        if code not in active_3 and code in country.STILL_ACTIVE_ALPHA3:
            problems.append(f"{code} is recorded as reissued but the register does not have it")
        if not entry.successors:
            problems.append(f"{code} names no successor")
        # Every successor has to be a code in use now, or one the table itself
        # explains. Following it has to end somewhere the register knows.
        for successor in entry.successors:
            if successor not in active_2 and successor not in country.alpha2_table():
                problems.append(
                    f"{code} names {successor} as a successor, which the register "
                    f"has never heard of"
                )
        steps = country.chain(code)
        unresolved = [s for s in steps if s not in active_2]
        if not steps:
            problems.append(f"{code} leads nowhere")
        elif all(s not in active_2 for s in steps):
            problems.append(f"{code} leads to {', '.join(steps)}, none of which are active")
        elif unresolved and not any(
            s in country.alpha2_table() for s in unresolved
        ):  # a dead step is only allowed when the table explains it
            problems.append(f"{code} leads through {', '.join(unresolved)}, which is unexplained")
        check_date(code, entry.effective, problems, exact=False)
        if not entry.note.endswith("."):
            problems.append(f"{code} has a note that is not a sentence")

    # The codes held back must really be held back, or the exclusions are
    # silently hiding real findings.
    for alpha2, meaning in sorted(country.ALPHA2_STILL_ACTIVE.items()):
        if alpha2 not in active_2:
            problems.append(f"{alpha2} is excluded as still active, but the register dropped it")
        if not meaning.strip():
            problems.append(f"{alpha2} is excluded without saying what it means now")
    for alpha2 in sorted(country.alpha2_table()):
        if alpha2 in active_2:
            problems.append(f"{alpha2} is reported as retired but is in the register")

    if not problems:
        print(
            f"ok: ISO 3166, {len(country.RETIRED)} retired codes "
            f"({len(country.reportable())} reportable, {len(country.alpha2_table())} alpha-2), "
            f"matched against {len(register)} ISO 3166-3 entries and "
            f"{len(active_3)} active countries"
        )
    return problems


def main() -> int:
    problems = verify_currency() + verify_country()
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
