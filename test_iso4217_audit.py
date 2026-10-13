from __future__ import annotations

import pathlib

import pytest

import iso4217_audit as audit
from iso4217_audit.table import WITHDRAWN, chain


def test_finds_a_withdrawn_code():
    findings = audit.scan_text("currency: SLL\n")
    assert [f.code for f in findings] == ["SLL"]
    assert findings[0].line_number == 1
    assert findings[0].withdrawal.successor == "SLE"


def test_ignores_an_active_code():
    assert audit.scan_text("currency: USD\nother: EUR\n") == []


@pytest.mark.parametrize(
    "line",
    [
        "angle = 90",          # lower case
        "const ANGLE = 90",    # longer token
        "CHANGE_ME = 1",       # inside an identifier
        "x.ANGx = 1",          # followed by a letter
        "A_ANG = 1",           # preceded by an underscore
    ],
)
def test_does_not_match_inside_a_longer_word(line):
    assert audit.scan_text(line) == [], line


@pytest.mark.parametrize("line", ["ANG", '"ANG"', "- ANG", "{ANG}", "ANG,EUR", "(ANG)"])
def test_matches_a_standalone_token(line):
    assert [f.code for f in audit.scan_text(line)] == ["ANG"], line


def test_reports_every_occurrence_with_its_line():
    text = "a: SLL\nb: USD\nc: SLL\n"
    findings = audit.scan_text(text)
    assert [(f.line_number, f.code) for f in findings] == [(1, "SLL"), (3, "SLL")]


def test_scan_path_walks_a_tree_and_honours_extensions(tmp_path):
    (tmp_path / "data.yml").write_text("- SLL\n")
    (tmp_path / "notes.md").write_text("- SLL\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.yml").write_text("- SLL\n")

    everything = audit.scan_path(tmp_path)
    assert sorted(f.path.name for f in everything) == ["data.yml", "notes.md"]

    only_yaml = audit.scan_path(tmp_path, extensions={"yml"})
    assert [f.path.name for f in only_yaml] == ["data.yml"]


def test_binary_and_oversized_files_are_skipped(tmp_path):
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe SLL")
    (tmp_path / "huge.yml").write_text("SLL\n" + "x" * 100)
    assert audit.scan_path(tmp_path, max_bytes=50) == []


def test_cli_exit_codes_and_ignore(tmp_path, capsys):
    target = tmp_path / "data.yml"
    target.write_text("- SLL\n- HRK\n")

    assert audit.main([str(target), "--quiet"]) == 1
    assert "2 withdrawn code(s): HRK, SLL" in capsys.readouterr().out

    assert audit.main([str(target), "--quiet", "--ignore", "sll,hrk"]) == 0


def test_cli_since_filters_by_date(tmp_path, capsys):
    target = tmp_path / "data.yml"
    # ITL went in 1999, ZWL in 2024.
    target.write_text("- ITL\n- ZWL\n")
    assert audit.main([str(target), "--quiet", "--since", "2020-01-01"]) == 1
    assert "1 withdrawn code(s): ZWL" in capsys.readouterr().out


def test_cli_list(capsys):
    assert audit.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "ANG -> XCG, 2025-03-31" in out
    assert out.count("\n") == len(WITHDRAWN)


def test_clean_tree_exits_zero(tmp_path):
    (tmp_path / "data.yml").write_text("- USD\n- EUR\n")
    assert audit.main([str(tmp_path), "--quiet"]) == 0


def test_every_entry_is_described_in_a_sentence():
    for code in WITHDRAWN:
        text = audit.describe(code)
        assert text.startswith(code)
        assert text.endswith(".")


def test_chain_follows_repeated_replacements():
    # VEB became VEF in 2008 and VEF became VES in 2018.
    assert chain("VEB") == ["VEF", "VES"]
    assert chain("SLL") == ["SLE"]
    assert chain("HRK") == []


def test_describe_names_the_code_in_use_now():
    assert "VEF has since been replaced by VES." in audit.describe("VEB")
    assert "has since been replaced" not in audit.describe("SLL")
