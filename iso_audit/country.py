"""Country codes ISO 3166 has retired, and what replaced them.

ISO 3166-3 is the part of the standard that records codes 3166-1 used to
contain. Every entry there has a four-letter code whose first two letters are
the retired alpha-2 and whose last two say where it went: a real country code
for a single successor, `HH` when the entity was divided, `XX` when no
successor was assigned, `AA` when the same alpha-2 was reissued for the same
place. That four-letter code is the citation for each row below.

Two kinds of collision make this table narrower than the register:

  * A retired alpha-2 can be handed to a different country later. `SK` was
    Sikkim until 1975 and has been Slovakia since 1993. A codebase using `SK`
    is almost certainly right, so those codes are recorded and never reported.
  * A retired alpha-3 can be an active code in another standard. `ZAR` was
    Zaire and is the South African rand; `GEL` was the Gilbert and Ellice
    Islands and is the Georgian lari. That is why country codes and currency
    codes cannot be scanned for at the same time.

`verify.py` checks every row against the current register.
"""

from __future__ import annotations

from typing import NamedTuple


class Retirement(NamedTuple):
    alpha_2: str
    alpha_4: str | None  # the ISO 3166-3 entry, or None for a 3166-1 code change
    successors: tuple[str, ...]  # current alpha-2 codes
    effective: str  # YYYY or YYYY-MM-DD, at the precision ISO published
    note: str


# Keyed by the retired alpha-3, which is the form worth grepping for: alpha-2
# codes are two upper-case letters and collide with ordinary identifiers.
RETIRED: dict[str, Retirement] = {
    # Dissolved into several successors.
    "ANT": Retirement("AN", "ANHH", ("BQ", "CW", "SX"), "2010-12-15",
                      "The Netherlands Antilles were dissolved."),
    "ATF": Retirement("FQ", "FQHH", ("TF", "AQ"), "1979",
                      "The French Southern and Antarctic Territories were split; TF kept "
                      "the alpha-3 ATF, so this code is recorded but never reported."),
    "CSK": Retirement("CS", "CSHH", ("CZ", "SK"), "1993-06-15",
                      "Czechoslovakia was dissolved."),
    "GEL": Retirement("GE", "GEHH", ("KI", "TV"), "1979",
                      "The Gilbert and Ellice Islands were split."),
    "NTZ": Retirement("NT", "NTHH", ("IQ", "SA"), "1993-07-12",
                      "The Saudi-Iraqi Neutral Zone was partitioned."),
    "PCI": Retirement("PC", "PCHH", ("FM", "MH", "MP", "PW"), "1986",
                      "The Trust Territory of the Pacific Islands was dissolved."),
    "SCG": Retirement("CS", "CSXX", ("RS", "ME"), "2006-09-26",
                      "Serbia and Montenegro separated."),
    "SUN": Retirement("SU", "SUHH",
                      ("RU", "AM", "AZ", "BY", "EE", "GE", "KZ", "KG", "LV", "LT",
                       "MD", "TJ", "TM", "UA", "UZ"), "1992-08-30",
                      "The USSR was dissolved."),
    "YUG": Retirement("YU", "YUCS", ("CS",), "2003-07-23",
                      "Yugoslavia became Serbia and Montenegro, which then separated."),
    # Renamed, reconstituted, or absorbed, with one successor.
    "AFI": Retirement("AI", "AIDJ", ("DJ",), "1977",
                      "French Afars and Issas became Djibouti."),
    "ATB": Retirement("BQ", "BQAQ", ("AQ",), "1979",
                      "The British Antarctic Territory was absorbed into Antarctica."),
    "ATN": Retirement("NQ", "NQAQ", ("AQ",), "1983",
                      "Dronning Maud Land was absorbed into Antarctica."),
    "BUR": Retirement("BU", "BUMM", ("MM",), "1989-12-05",
                      "Burma was renamed Myanmar."),
    "BYS": Retirement("BY", "BYAA", ("BY",), "1992-06-15",
                      "The Byelorussian SSR became Belarus, keeping the alpha-2 BY."),
    "CTE": Retirement("CT", "CTKI", ("KI",), "1984",
                      "The Canton and Enderbury Islands joined Kiribati."),
    "DDR": Retirement("DD", "DDDE", ("DE",), "1990-10-30",
                      "The German Democratic Republic acceded to Germany."),
    "DHY": Retirement("DY", "DYBJ", ("BJ",), "1977",
                      "Dahomey was renamed Benin."),
    "FXX": Retirement("FX", "FXFR", ("FR",), "1997-07-14",
                      "Metropolitan France stopped being coded separately."),
    "HVO": Retirement("HV", "HVBF", ("BF",), "1984",
                      "Upper Volta was renamed Burkina Faso."),
    "JTN": Retirement("JT", "JTUM", ("UM",), "1986",
                      "Johnston Island joined the US Minor Outlying Islands."),
    "MID": Retirement("MI", "MIUM", ("UM",), "1986",
                      "The Midway Islands joined the US Minor Outlying Islands."),
    "NHB": Retirement("NH", "NHVU", ("VU",), "1980",
                      "The New Hebrides became Vanuatu."),
    "PCZ": Retirement("PZ", "PZPA", ("PA",), "1980",
                      "The Panama Canal Zone was returned to Panama."),
    "PUS": Retirement("PU", "PUUM", ("UM",), "1986",
                      "The US Miscellaneous Pacific Islands were merged into UM."),
    "RHO": Retirement("RH", "RHZW", ("ZW",), "1980",
                      "Southern Rhodesia became Zimbabwe."),
    "ROM": Retirement("RO", None, ("RO",), "2002-02-01",
                      "Romania's alpha-3 changed from ROM to ROU; its alpha-2 did not "
                      "change. This is a 3166-1 correction, not a 3166-3 entry."),
    "SKM": Retirement("SK", "SKIN", ("IN",), "1975",
                      "Sikkim was annexed by India."),
    "TMP": Retirement("TP", "TPTL", ("TL",), "2002-05-20",
                      "East Timor became Timor-Leste."),
    "VDR": Retirement("VD", "VDVN", ("VN",), "1977",
                      "North Vietnam was reunified into Viet Nam."),
    "WAK": Retirement("WK", "WKUM", ("UM",), "1986",
                      "Wake Island joined the US Minor Outlying Islands."),
    "YMD": Retirement("YD", "YDYE", ("YE",), "1990-08-14",
                      "South Yemen was reunified into Yemen."),
    "ZAR": Retirement("ZR", "ZRCD", ("CD",), "1997-07-14",
                      "Zaire became the Democratic Republic of the Congo."),
}

# Retired alpha-3 codes that the register still assigns to a living entity.
# TF took over ATF when FQ was split, so finding ATF in a codebase says
# nothing. Reporting it would be wrong every time.
STILL_ACTIVE_ALPHA3 = frozenset({"ATF"})

# Alpha-2 codes that appear above but are in the register today. Two different
# things end up here and both mean "do not report this": a code handed to
# another country (SK was Sikkim, now Slovakia), and a code that never went
# away because only the alpha-3 changed (RO, BY). Each maps to what it means
# now. These are why alpha-2 codes are checked against an explicit list of
# codes and never grepped for.
ALPHA2_STILL_ACTIVE: dict[str, str] = {
    "AI": "Anguilla, which took the code over from French Afars and Issas",
    "BQ": "Bonaire, Sint Eustatius and Saba, which took it over from the "
          "British Antarctic Territory",
    "BY": "Belarus, the same place the Byelorussian SSR was",
    "GE": "Georgia, which took it over from the Gilbert and Ellice Islands",
    "RO": "Romania, whose alpha-2 never changed when ROM became ROU",
    "SK": "Slovakia, which took it over from Sikkim",
}


def reportable() -> dict[str, Retirement]:
    """The rows safe to report on sight, by retired alpha-3."""
    return {code: entry for code, entry in RETIRED.items() if code not in STILL_ACTIVE_ALPHA3}


def alpha2_table() -> dict[str, str]:
    """Retired alpha-2 codes to their alpha-3, excluding any still assigned."""
    table: dict[str, str] = {}
    for alpha3, entry in RETIRED.items():
        if entry.alpha_2 in ALPHA2_STILL_ACTIVE:
            continue
        # CS was Czechoslovakia until 1993 and Serbia and Montenegro until
        # 2006. Both are retired, and the later use is the one a codebase
        # written this century is likelier to have meant.
        existing = table.get(entry.alpha_2)
        if existing is None or entry.effective > RETIRED[existing].effective:
            table[entry.alpha_2] = alpha3
    return table


def _retirement_of_alpha2(alpha_2: str, after: str) -> str | None:
    """The alpha-3 of the entry that retired `alpha_2` next after `after`.

    CS names two entries, so the successor has to be resolved by date rather
    than by whichever one a dict happened to keep.
    """
    candidates = [
        alpha3
        for alpha3, entry in RETIRED.items()
        if entry.alpha_2 == alpha_2 and entry.effective > after
    ]
    return min(candidates, key=lambda c: RETIRED[c].effective) if candidates else None


def chain(code: str) -> list[str]:
    """Successors of a retired alpha-3, following further retirements.

    YUG names CS, which was itself retired in 2006, so the code the standard
    hands you is not always one in use now.
    """
    out: list[str] = []
    queue = [(s, RETIRED[code].effective) for s in RETIRED[code].successors]
    # Not seeded with this entry's own alpha-2: an entry may legitimately name
    # it as the successor, which is what the `AA` suffix means. BYAA says the
    # Byelorussian SSR became Belarus and kept BY.
    seen: set[str] = set()
    while queue:
        current, after = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        out.append(current)
        later = _retirement_of_alpha2(current, after)
        if later:
            queue.extend((s, RETIRED[later].effective) for s in RETIRED[later].successors)
    return out


def describe(code: str) -> str:
    """One line saying what happened to a retired country code."""
    entry = RETIRED[code]
    where = f" (ISO 3166-3 {entry.alpha_4})" if entry.alpha_4 else " (ISO 3166-1 change)"
    successors = ", ".join(entry.successors)
    line = f"{code}/{entry.alpha_2} -> {successors}, {entry.effective}{where}: {entry.note}"
    live = [c for c in chain(code) if c not in alpha2_table()]
    if list(entry.successors) != live:
        line += f" In the register today that is {', '.join(live)}."
    if code in STILL_ACTIVE_ALPHA3:
        line += " The alpha-3 is still in use, so it is never reported."
    return line
