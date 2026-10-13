# iso4217-audit

Find the currency codes a codebase still uses after ISO 4217 withdrew them.

Currency lists get copied out of the ISO table once and then sit there.
Sierra Leone redenominated in 2022, Zimbabwe issued a new currency in 2024,
the Caribbean guilder replaced the Netherlands Antillean guilder in 2025,
Bulgaria joined the euro in 2026 — and a generator or a validator built on the
old table keeps handing out codes that nothing accepts any more.

```console
$ iso4217-audit lib/locales/en/currency.yml
lib/locales/en/currency.yml:5: ANG -> XCG, 2025-03-31: Netherlands Antillean guilder replaced by the Caribbean guilder.
    - ANG
lib/locales/en/currency.yml:15: BGN withdrawn 2026-01-01: Bulgaria adopted the euro (EUR).
    - BGN
...
13 occurrence(s) of 13 withdrawn code(s): ANG, BGN, BYR, EEK, HRK, LTL, LVL, MRO, SLL, STD, VEF, ZMK, ZWL
```

That is a real run against [faker-ruby](https://github.com/faker-ruby/faker)
before [#3335](https://github.com/faker-ruby/faker/pull/3335).

## Install

```console
$ pipx install git+https://github.com/yu2971512385-ui/iso4217-audit
```

Standard library only, Python 3.10 or newer. `pycountry` is needed to verify
the table, not to use it.

## Use

```console
$ iso4217-audit .                        # every file in the tree
$ iso4217-audit --ext yml,json,rb data/  # only these extensions
$ iso4217-audit --since 2015-01-01 .     # ignore the old euro-zone changes
$ iso4217-audit --ignore ANG,HRK .       # a table that is historical on purpose
$ iso4217-audit --list                   # print what the tool knows
```

Exit status is 1 when something turns up, so it drops into CI as it is.

A code is reported only where it stands as its own upper-case token, so
`ANGLE`, `CHANGE` and `ang` are left alone. That rule is what keeps the output
short enough to read; it also means a code spelled across a string
concatenation will be missed.

### As a library

```python
from iso4217_audit import scan_text, describe
from iso4217_audit.table import WITHDRAWN, chain

for finding in scan_text(open("currencies.yml").read()):
    print(finding.code, finding.withdrawal.successor)

chain("VEB")        # ['VEF', 'VES'] -- replaced twice
describe("ZWL")     # 'ZWL -> ZWG, 2024-04-05: ...'
WITHDRAWN["HRK"]    # Withdrawal(successor=None, effective='2023-01-01', ...)
```

## Keeping the table honest

`verify.py` reads the current register from `pycountry` and checks two things,
either of which failing means the table claims something the register does not
support:

- no code called withdrawn here may still be active,
- following the successors has to arrive at one that is.

```console
$ python verify.py
ok: 41 withdrawn codes, 19 with a successor, checked against 178 active codes
```

CI runs it on every push and once a week, so a currency change shows up as a
failure rather than as silence.

## What it covers

41 codes: the redenominations and renamings since 1999, the national
currencies withdrawn on joining the euro, and the Cuban convertible peso. It
is not the complete history of ISO 4217 — codes retired before 1999 are out —
and it is deliberately quiet about anything it cannot state with a date.

## Licence

MIT.
