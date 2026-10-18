"""Currency codes ISO 4217 has withdrawn, and what replaced them.

Each entry is (successor or None, date the change took effect, what happened).
A successor of None means the country stopped issuing its own currency and
adopted one already in the list, which is named in the note.

`verify.py` checks every row against the current ISO 4217 register: no code
here may still be active, and following the successors has to arrive at one
that is.
"""

from __future__ import annotations

from typing import NamedTuple


class Withdrawal(NamedTuple):
    successor: str | None
    effective: str
    note: str


WITHDRAWN: dict[str, Withdrawal] = {
    # Redenominations and renamings.
    "AFA": Withdrawal("AFN", "2003-01-01", "Afghan afghani redenominated."),
    "ANG": Withdrawal("XCG", "2025-03-31", "Netherlands Antillean guilder replaced by the Caribbean guilder."),
    "AZM": Withdrawal("AZN", "2006-01-01", "Azerbaijani manat redenominated."),
    "BYR": Withdrawal("BYN", "2016-07-01", "Belarusian ruble redenominated."),
    "GHC": Withdrawal("GHS", "2007-07-01", "Ghanaian cedi redenominated."),
    "MRO": Withdrawal("MRU", "2018-01-01", "Mauritanian ouguiya redenominated."),
    "MZM": Withdrawal("MZN", "2006-07-01", "Mozambican metical redenominated."),
    "ROL": Withdrawal("RON", "2005-07-01", "Romanian leu redenominated."),
    "SDD": Withdrawal("SDG", "2007-01-01", "Sudanese dinar replaced by the pound."),
    "SLL": Withdrawal("SLE", "2022-04-01", "Sierra Leonean leone redenominated."),
    "SRG": Withdrawal("SRD", "2004-01-01", "Surinamese guilder replaced by the dollar."),
    "STD": Withdrawal("STN", "2018-01-01", "Sao Tome and Principe dobra redenominated."),
    "TMM": Withdrawal("TMT", "2009-01-01", "Turkmenistani manat redenominated."),
    "TRL": Withdrawal("TRY", "2005-01-01", "Turkish lira redenominated."),
    "VEB": Withdrawal("VEF", "2008-01-01", "Venezuelan bolivar redenominated."),
    "VEF": Withdrawal("VES", "2018-08-20", "Venezuelan bolivar redenominated again."),
    "ZMK": Withdrawal("ZMW", "2013-01-01", "Zambian kwacha redenominated."),
    "ZWD": Withdrawal("ZWL", "2009-02-02", "Zimbabwean dollar redenominated."),
    "ZWL": Withdrawal("ZWG", "2024-04-05", "Zimbabwe dollar replaced by Zimbabwe Gold."),
    # Withdrawn on joining the euro.
    "ATS": Withdrawal(None, "1999-01-01", "Austria adopted the euro (EUR)."),
    "BEF": Withdrawal(None, "1999-01-01", "Belgium adopted the euro (EUR)."),
    "BGN": Withdrawal(None, "2026-01-01", "Bulgaria adopted the euro (EUR)."),
    "CYP": Withdrawal(None, "2008-01-01", "Cyprus adopted the euro (EUR)."),
    "DEM": Withdrawal(None, "1999-01-01", "Germany adopted the euro (EUR)."),
    "EEK": Withdrawal(None, "2011-01-01", "Estonia adopted the euro (EUR)."),
    "ESP": Withdrawal(None, "1999-01-01", "Spain adopted the euro (EUR)."),
    "FIM": Withdrawal(None, "1999-01-01", "Finland adopted the euro (EUR)."),
    "FRF": Withdrawal(None, "1999-01-01", "France adopted the euro (EUR)."),
    "GRD": Withdrawal(None, "2001-01-01", "Greece adopted the euro (EUR)."),
    "HRK": Withdrawal(None, "2023-01-01", "Croatia adopted the euro (EUR)."),
    "IEP": Withdrawal(None, "1999-01-01", "Ireland adopted the euro (EUR)."),
    "ITL": Withdrawal(None, "1999-01-01", "Italy adopted the euro (EUR)."),
    "LTL": Withdrawal(None, "2015-01-01", "Lithuania adopted the euro (EUR)."),
    "LUF": Withdrawal(None, "1999-01-01", "Luxembourg adopted the euro (EUR)."),
    "LVL": Withdrawal(None, "2014-01-01", "Latvia adopted the euro (EUR)."),
    "MTL": Withdrawal(None, "2008-01-01", "Malta adopted the euro (EUR)."),
    "NLG": Withdrawal(None, "1999-01-01", "the Netherlands adopted the euro (EUR)."),
    "PTE": Withdrawal(None, "1999-01-01", "Portugal adopted the euro (EUR)."),
    "SIT": Withdrawal(None, "2007-01-01", "Slovenia adopted the euro (EUR)."),
    "SKK": Withdrawal(None, "2009-01-01", "Slovakia adopted the euro (EUR)."),
    # Withdrawn without a successor code.
    "CUC": Withdrawal(None, "2021-06-30", "Cuba withdrew the convertible peso; CUP remains."),
}


def chain(code: str) -> list[str]:
    """The successors of `code`, in order, as far as the table goes.

    A currency can be replaced more than once -- VEB became VEF in 2008 and
    VEF became VES in 2018 -- so the immediate successor is not always the one
    in use now.
    """
    seen = [code]
    current = WITHDRAWN[code].successor
    while current is not None:
        if current in seen:  # a cycle would mean the table contradicts itself
            break
        seen.append(current)
        if current not in WITHDRAWN:
            break
        current = WITHDRAWN[current].successor
    return seen[1:]


def describe(code: str) -> str:
    """One line saying what happened to a withdrawn code."""
    entry = WITHDRAWN[code]
    if not entry.successor:
        return f"{code} withdrawn {entry.effective}: {entry.note}"
    line = f"{code} -> {entry.successor}, {entry.effective}: {entry.note}"
    rest = chain(code)[1:]
    if rest:
        line += f" {entry.successor} has since been replaced by {rest[-1]}."
    return line
