import shutil
from pathlib import Path

import pytest
from build import Finding, Kind, Severity, main, parse_bibtex_log, parse_log, unwrap

FIXTURES = Path(__file__).parent / "fixtures" / "logs"


def read_fixture(name: str) -> list[Finding]:
    return parse_log((FIXTURES / name).read_bytes())


def of_kind(findings: list[Finding], kind: Kind) -> list[Finding]:
    return [finding for finding in findings if finding.kind is kind]


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("fixture", ["lualatex-warnings.log", "pdflatex-warnings.log"])
@pytest.mark.parametrize(
    "kind",
    [
        Kind.UNDEFINED_REFERENCE,
        Kind.UNDEFINED_CITATION,
        Kind.MULTIPLY_DEFINED_LABEL,
        Kind.OVERFULL_BOX,
        Kind.UNDERFULL_BOX,
        Kind.FONT_SUBSTITUTION,
        Kind.MISSING_GLYPH,
    ],
)
def test_finds_each_defect_kind_in_recorded_logs(fixture: str, kind: Kind) -> None:
    found = of_kind(read_fixture(fixture), kind)

    assert found
    assert all(finding.severity is Severity.DEFECT for finding in found)


def test_locates_warnings_by_file_and_input_line() -> None:
    findings = read_fixture("lualatex-warnings.log")

    located = {(finding.kind, finding.file, finding.line) for finding in findings}

    assert (Kind.UNDEFINED_REFERENCE, "warnings-lualatex.tex", 8) in located
    assert (Kind.OVERFULL_BOX, "warnings-lualatex.tex", 10) in located
    assert (Kind.UNDERFULL_BOX, "warnings-lualatex.tex", 13) in located
    assert (Kind.FONT_SUBSTITUTION, "warnings-lualatex.tex", 16) in located


def test_rejoins_a_citation_warning_wrapped_across_lines() -> None:
    (citation,) = of_kind(read_fixture("lualatex-warnings.log"), Kind.UNDEFINED_CITATION)

    assert citation.line == 8
    assert "nobody2020" in citation.message


def test_rejoins_a_missing_glyph_line_luatex_wrapped_at_eighty_bytes() -> None:
    glyphs = of_kind(read_fixture("lualatex-warnings.log"), Kind.MISSING_GLYPH)

    assert glyphs
    assert all("U+2603" in glyph.message and "+tlig" in glyph.message for glyph in glyphs)


def test_does_not_report_end_of_run_summaries() -> None:
    findings = read_fixture("lualatex-warnings.log") + read_fixture("pdflatex-warnings.log")

    assert not [finding for finding in findings if "There were" in finding.message]


def test_reads_an_error_with_file_and_line_prefix() -> None:
    assert read_fixture("lualatex-error.log") == [
        Finding(Kind.ERROR, Severity.DEFECT, "Undefined control sequence.", "error.tex", 5)
    ]


def test_reads_a_classic_error_and_takes_its_line_from_the_context() -> None:
    assert read_fixture("pdflatex-error.log") == [
        Finding(
            Kind.ERROR,
            Severity.DEFECT,
            "LaTeX Error: Environment derivation undefined.",
            "error-classic.tex",
            5,
        )
    ]


def test_attributes_findings_to_input_files_whose_paths_have_spaces() -> None:
    boxes = of_kind(read_fixture("multi-file.log"), Kind.OVERFULL_BOX)

    assert [(box.file, box.line) for box in boxes] == [
        ("chapter one/intro.tex", 5),
        ("main.tex", 7),
    ]


@pytest.mark.parametrize(
    ("header", "severity"),
    [
        (rb"Overfull \hbox (0.4pt too wide) in paragraph at lines 3--4", Severity.WARNING),
        (rb"Overfull \hbox (2.5pt too wide) in paragraph at lines 3--4", Severity.DEFECT),
        (rb"Underfull \hbox (badness 1500) in paragraph at lines 3--4", Severity.WARNING),
        (rb"Underfull \hbox (badness 10000) in paragraph at lines 3--4", Severity.DEFECT),
        (
            rb"Overfull \vbox (12.0pt too high) has occurred while \output is active",
            Severity.DEFECT,
        ),
    ],
)
def test_grades_boxes_against_their_thresholds(header: bytes, severity: Severity) -> None:
    log = header + b"\n[]\\OT1/cmr/m/n/10 a (line\n\n"

    (box,) = parse_log(log)

    assert box.severity is severity


def test_reports_other_package_warnings_as_warnings() -> None:
    log = b"Package hyperref Warning: Token not allowed in a PDF string (Unicode):\n"
    log += b"(hyperref)                removing `math shift' on input line 12.\n\n"

    (warning,) = parse_log(log)

    assert warning.kind is Kind.WARNING
    assert warning.severity is Severity.WARNING
    assert warning.line == 12
    assert "removing `math shift'" in warning.message


def test_keeps_a_message_that_starts_straight_after_a_full_line() -> None:
    full_line = b"x" * 79

    assert unwrap(full_line + b"\n! Undefined control sequence.\n") == [
        full_line.decode(),
        "! Undefined control sequence.",
    ]


def test_finds_nothing_in_an_empty_log() -> None:
    assert parse_log(b"") == []


def test_reads_bibtex_errors_as_defects_and_warnings_as_warnings() -> None:
    findings = parse_bibtex_log((FIXTURES / "bibtex-missing-database.blg").read_bytes())

    assert findings == [
        Finding(
            Kind.BIBLIOGRAPHY,
            Severity.DEFECT,
            "I couldn't open database file refs.bib",
            "cite.aux",
            5,
        ),
        Finding(Kind.BIBLIOGRAPHY, Severity.DEFECT, "I found no database files", "cite.aux"),
        Finding(
            Kind.BIBLIOGRAPHY, Severity.WARNING, 'I didn\'t find a database entry for "ising1925"'
        ),
        Finding(
            Kind.BIBLIOGRAPHY, Severity.WARNING, 'I didn\'t find a database entry for "absent2020"'
        ),
    ]


CLEAN_DOCUMENT = r"""\documentclass{article}
\begin{document}
A short paragraph that sets without trouble.
\end{document}
"""

BROKEN_DOCUMENT = r"""\documentclass{article}
\begin{document}
The value is \undefinedmacro{3}.
\end{document}
"""

LOOPING_DOCUMENT = r"""\documentclass{article}
\begin{document}
\def\forever{\forever}\forever
\end{document}
"""

CITING_DOCUMENT = r"""\documentclass{article}
\usepackage{natbib}
\begin{document}
See \citet{ising1925}.
\bibliographystyle{plainnat}
\bibliography{refs}
\end{document}
"""

BIBLIOGRAPHY = """@article{ising1925,
  author = {Ising, Ernst},
  title = {Beitrag zur Theorie des Ferromagnetismus},
  journal = {Z. Phys.},
  volume = {31},
  pages = {253--258},
  year = {1925},
}
"""


@pytest.mark.tex
def test_reports_a_clean_build_in_a_folder_with_spaces(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write(tmp_path / "my report" / "main.tex", CLEAN_DOCUMENT)

    exit_code = main([str(document)])

    assert exit_code == 0
    assert "0 defects" in capsys.readouterr().out
    assert (document.parent / "build" / "main.pdf").is_file()


@pytest.mark.tex
def test_reports_an_error_in_a_broken_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write(tmp_path / "main.tex", BROKEN_DOCUMENT)

    exit_code = main([str(document), "--engine", "pdflatex"])

    assert exit_code == 1
    assert "main.tex:3  Undefined control sequence." in capsys.readouterr().out


@pytest.mark.tex
def test_stops_a_looping_build_at_the_timeout_and_leaves_no_engine_running(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write(tmp_path / "loop" / "main.tex", LOOPING_DOCUMENT)

    exit_code = main([str(document), "--engine", "pdflatex", "--timeout-seconds", "5"])

    assert exit_code == 1
    assert "latexmk stopped after 5 s" in capsys.readouterr().out
    # A surviving engine would hold its log open, and Windows refuses to delete it.
    shutil.rmtree(document.parent)


@pytest.mark.tex
def test_finds_a_bibliography_beside_the_document_when_building_elsewhere(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write(tmp_path / "main.tex", CITING_DOCUMENT)
    write(tmp_path / "refs.bib", BIBLIOGRAPHY)

    exit_code = main([str(document), "--engine", "pdflatex"])

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "citation" not in output


def test_rejects_a_path_that_is_not_a_tex_file(tmp_path: Path) -> None:
    document = write(tmp_path / "notes.md", "# Notes\n")

    assert main([str(document)]) == 2
