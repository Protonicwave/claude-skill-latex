import re
from collections import Counter
from pathlib import Path

import lint
import pytest
from lint import Finding, Rule, Severity, main

FIXTURES = Path(__file__).parent / "fixtures" / "tex"
CASES = ("defects", "tells", "ignored", "template", "multi-file")
# A fixture line names the rules it should trigger in a trailing comment, which
# the lint itself ignores like any other comment.
ANNOTATION = re.compile(r"%\s*(?P<kind>lint|suppressed):\s*(?P<rules>[\w, -]+?)\s*$")

# Counted, not collected, so a rule reported twice on one line must be annotated twice.
Located = Counter[tuple[str, int, str]]


def annotations(case: str, kind: str) -> Located:
    folder = FIXTURES / case
    expected: Located = Counter()
    for path in folder.rglob("*.tex"):
        name = path.relative_to(folder).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, text in enumerate(lines, start=1):
            match = ANNOTATION.search(text)
            if match is not None and match.group("kind") == kind:
                rules = match.group("rules").split(",")
                expected.update((name, number, rule.strip()) for rule in rules)
    return expected


def located(findings: tuple[Finding, ...]) -> Located:
    return Counter((finding.file, finding.line, finding.rule.rule_id) for finding in findings)


def write(path: Path, text: str, newline: str = "\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    return path


@pytest.mark.parametrize("case", CASES)
def test_reports_exactly_the_annotated_findings(case: str) -> None:
    result = lint.lint(FIXTURES / case / "main.tex")

    assert located(result.findings) == annotations(case, "lint")


@pytest.mark.parametrize("case", CASES)
def test_suppresses_exactly_the_annotated_house_style_tells(case: str) -> None:
    result = lint.lint(FIXTURES / case / "main.tex")

    assert located(result.suppressed) == annotations(case, "suppressed")


def test_every_rule_is_exercised_by_a_fixture() -> None:
    rules = {value.rule_id for value in vars(lint).values() if isinstance(value, Rule)}
    exercised = {
        rule
        for case in CASES
        for kind in ("lint", "suppressed")
        for _, _, rule in annotations(case, kind)
    }

    assert rules == exercised


def test_suppresses_only_tells_never_defects() -> None:
    result = lint.lint(FIXTURES / "template" / "main.tex")

    assert all(finding.rule.severity is Severity.TELL for finding in result.suppressed)
    assert all(finding.rule.is_house_style for finding in result.suppressed)


def test_reads_windows_line_endings_without_shifting_lines(tmp_path: Path) -> None:
    document = write(
        tmp_path / "main.tex",
        "Text before.\n\n\\begin{equation}\n  x = 1\n\\end{equation}\n",
        newline="\r\n",
    )

    (finding,) = lint.lint(document).findings

    assert (finding.rule.rule_id, finding.line) == ("blank-line-before-display", 3)


def test_finds_nothing_in_an_empty_file(tmp_path: Path) -> None:
    result = lint.lint(write(tmp_path / "main.tex", ""))

    assert result.findings == ()


def test_reads_a_file_that_inputs_itself_once(tmp_path: Path) -> None:
    document = write(tmp_path / "main.tex", "\\input{main}\nPages 3-5.\n")

    result = lint.lint(document)

    assert located(result.findings) == Counter({("main.tex", 2, "hyphen-range"): 1})
    assert result.files_read == 1


@pytest.mark.parametrize(
    ("limit", "value", "reason"),
    [("MAX_FILES", 2, "more than 2 files"), ("MAX_FILE_BYTES", 40, "larger than 40 bytes")],
)
def test_reports_inputs_beyond_a_limit_as_unread(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str, value: int, reason: str
) -> None:
    write(tmp_path / "one.tex", "One.\n")
    write(tmp_path / "two.tex", "Two, padded to pass the byte limit set by the test.\n")
    document = write(tmp_path / "main.tex", "\\input{one}\n\\input{two}\n")
    monkeypatch.setattr(lint, limit, value)

    (finding,) = lint.lint(document).findings

    assert (finding.rule.rule_id, finding.line) == ("unread-input", 2)
    assert reason in finding.excerpt


def test_follows_an_input_written_without_braces(tmp_path: Path) -> None:
    write(tmp_path / "chapter.tex", "Pages 3-5.\n")
    document = write(tmp_path / "main.tex", "\\input chapter\n")

    result = lint.lint(document)

    assert located(result.findings) == Counter({("chapter.tex", 1, "hyphen-range"): 1})
    assert result.files_read == 2


@pytest.mark.tex
def test_leaves_an_input_from_the_tex_distribution_unread_but_not_missing(
    tmp_path: Path,
) -> None:
    document = write(tmp_path / "main.tex", "\\input{glyphtounicode}\n\\input{absent}\n")

    (finding,) = lint.lint(document).findings

    assert (finding.rule.rule_id, finding.line) == ("unread-input", 2)


def test_reads_the_fonts_set_by_a_local_beamer_theme(tmp_path: Path) -> None:
    document = write(
        tmp_path / "main.tex",
        "\\documentclass{beamer}\n\\usetheme[dark]{House}\n\\begin{document}\n\\end{document}\n",
    )
    write(tmp_path / "beamerthemeHouse.sty", "\\usefonttheme{HouseType}\n")
    write(tmp_path / "beamerfontthemeHouseType.sty", "\\setmainfont{Erewhon}\n")

    assert lint.lint(document).findings == ()


@pytest.mark.parametrize(("case", "exit_code"), [("defects", 1), ("tells", 0), ("ignored", 0)])
def test_exits_with_one_only_for_defects(case: str, exit_code: int) -> None:
    assert main([str(FIXTURES / case / "main.tex")]) == exit_code


def test_reports_findings_by_location_and_counts_suppressed_tells(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main([str(FIXTURES / "template" / "main.tex")])

    output = capsys.readouterr().out
    assert "main.tex:17  hyphen-range" in output
    assert "5 house-style tells suppressed: class revtex4-2 sets the style" in output
    assert "hyphen-range (defect):" in output


@pytest.mark.parametrize("name", ["notes.md", "absent.tex"])
def test_rejects_a_path_that_is_not_an_existing_tex_file(tmp_path: Path, name: str) -> None:
    write(tmp_path / "notes.md", "# Notes\n")

    assert main([str(tmp_path / name)]) == 2


@pytest.mark.parametrize(
    ("main_text", "package_text"),
    [
        ("\\documentclass{article}\n% padded past the byte limit set by the test\n", ""),
        ("\\documentclass{article}\n\\usepackage{house}\n", "% padded past the limit\n" * 3),
    ],
)
def test_exits_with_two_when_the_document_or_a_local_package_is_too_large(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    main_text: str,
    package_text: str,
) -> None:
    document = write(tmp_path / "main.tex", main_text)
    write(tmp_path / "house.sty", package_text)
    monkeypatch.setattr(lint, "MAX_FILE_BYTES", 60)

    assert main([str(document)]) == 2
    assert "larger than 60 bytes" in capsys.readouterr().err
