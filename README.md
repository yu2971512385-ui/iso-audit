# iso-audit

Find the standard codes a codebase still uses after the standard withdrew
them: ISO 4217 currencies and ISO 3166 countries.

Code lists get copied out of the register once and then sit there. Sierra
Leone redenominated in 2022, Zimbabwe issued a new currency in 2024, the
Caribbean guilder replaced the Netherlands Antillean guilder in 2025, Bulgaria
joined the euro in 2026 — and a generator or a validator built on the old
table keeps handing out codes that nothing accepts any more. Country lists rot
more slowly and more quietly: `SU`, `YU`, `AN` and `TP` are still in files
that were written after the countries stopped existing.

```console
$ iso-audit lib/locales/en/currency.yml
lib/locales/en/currency.yml:5: ANG -> XCG, 2025-03-31: Netherlands Antillean guilder replaced by the Caribbean guilder.
    - ANG
lib/locales/en/currency.yml:15: BGN withdrawn 2026-01-01: Bulgaria adopted the euro (EUR).
    - BGN
...
13 occurrence(s) of 13 withdrawn currency code(s): ANG, BGN, BYR, EEK, HRK, LTL, LVL, MRO, SLL, STD, VEF, ZMK, ZWL
```

That is a real run against [faker-ruby](https://github.com/faker-ruby/faker)
before [#3335](https://github.com/faker-ruby/faker/pull/3335).

## Install

```console
$ pipx install git+https://github.com/yu2971512385-ui/iso-audit
```

Standard library only, Python 3.10 or newer. `pycountry` is needed to verify
the tables, not to use them.

## Use

```console
$ iso-audit .                           # currency codes, every file in the tree
$ iso-audit --standard country .        # country codes instead
$ iso-audit --ext yml,json,rb data/     # only these extensions
$ iso-audit --since 2015-01-01 .        # ignore the old euro-zone changes
$ iso-audit --ignore ANG,HRK .          # a table that is historical on purpose
$ iso-audit --standard country --codes countries.json
$ iso-audit --list                      # print what the tool knows
```

Exit status is 1 when something turns up, so it drops into CI as it is.

A code is reported only where it stands as its own upper-case token, so
`ANGLE`, `CHANGE` and `ang` are left alone. That rule is what keeps the output
short enough to read; it also means a code spelled across a string
concatenation will be missed.

### The two registers are not combined

`--standard` is not a convenience. `ZAR` is the South African rand and it is
the code ISO 3166 used for Zaire until 1997; `GEL` is the Georgian lari and
was the Gilbert and Ellice Islands until 1979. A scan that looked for both at
once would report every rand amount in a price list as a dead country. There
is no way to tell them apart from the token alone, so the tool asks which
register you mean and never guesses.

### Country codes come with three traps

Most of the country table is the list of things the tool refuses to say.

**A retired alpha-2 can be handed to another country.** `SK` was Sikkim until
1975 and has been Slovakia since 1993; `GE` was the Gilbert and Ellice
Islands and is Georgia; `AI` was French Afars and Issas and is Anguilla. A
codebase using any of them is almost certainly right, so they are recorded and
never reported.

**A retired alpha-3 can come back.** `ATF` was the French Southern and
Antarctic Territories, whose entry was retired in 1979 — and `ATF` is the
alpha-3 for French Southern Territories today. It is in the table and is
never reported.

**Two-letter codes are also most of a codebase.** `SU`, `AN`, `CS`, `DD` and
`NT` are real retired codes and ordinary identifiers. Grepping for them
produces noise and nothing else, so scanning looks only at three-letter codes.
Two-letter codes are checked with `--codes`, against a file that holds a list
of codes and nothing else, where `SU` can only mean the USSR:

```console
$ iso-audit --standard country --codes countries.json
SCG/CS -> RS, ME, 2006-09-26 (ISO 3166-3 CSXX): Serbia and Montenegro separated.
SUN/SU -> RU, AM, AZ, BY, EE, GE, KZ, KG, LV, LT, MD, TJ, TM, UA, UZ, 1992-08-30 (ISO 3166-3 SUHH): The USSR was dissolved.

251 code(s) checked, 2 withdrawn
```

### As a library

```python
from iso_audit import scan_text, check_codes, describe, COUNTRY
from iso_audit.currency import WITHDRAWN, chain
from iso_audit import country

for finding in scan_text(open("currencies.yml").read()):
    print(finding.code, finding.withdrawal.successor)

chain("VEB")                        # ['VEF', 'VES'] -- replaced twice
country.chain("YUG")                # ['CS', 'RS', 'ME'] -- retired twice
describe("ZWL")                     # 'ZWL -> ZWG, 2024-04-05: ...'
check_codes(["SU", "SK"], COUNTRY)  # SU only: SK is Slovakia
```

## Keeping the tables honest

`verify.py` reads the current registers from `pycountry`. For each table, two
things have to hold, either of which failing means the table claims something
the register does not support:

- no code called withdrawn here may still be active,
- following the successors has to arrive at codes that are.

The country table carries a third obligation: it has to match ISO 3166-3
entry for entry, citing each one's four-letter code, because its whole value
is being a list a maintainer does not have to assemble by hand.

```console
$ python verify.py
ok: ISO 4217, 41 withdrawn codes, 19 with a successor, checked against 178 active codes
ok: ISO 3166, 32 retired codes (31 reportable, 25 alpha-2), matched against 31 ISO 3166-3 entries and 249 active countries
```

It earns its keep. Writing the country table, it caught a successor chain that
dead-ended and an alpha-2 that had never been retired at all. Deleting a row,
inventing one, misciting a four-letter code, naming a country that does not
exist, or dropping one of the exclusions all fail it.

CI runs it on every push and once a week, so a change to either register shows
up as a failure rather than as silence.

## What it covers

**ISO 4217**: 41 codes — the redenominations and renamings since 1999, the
national currencies withdrawn on joining the euro, and the Cuban convertible
peso. Codes retired before 1999 are out.

**ISO 3166**: all 31 entries in ISO 3166-3, plus Romania's 2002 change from
`ROM` to `ROU`, which is a correction inside 3166-1 and has no 3166-3 entry.
One is held back from reporting and six two-letter codes are excluded, for the
reasons above.

Both tables are deliberately quiet about anything they cannot state with a
date.

## Licence

MIT.
