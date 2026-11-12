import re
import shutil
import subprocess
from pathlib import Path

import build
import pytest
from new_project import ASSETS, BEAMER_PACKAGES, DOCUMENT_PACKAGES

PDFTOTEXT_TIMEOUT_SECONDS = 60
MINUS_SIGN = "\N{MINUS SIGN}"

# Every macro laboratory-base.sty gives tables, tags and keys, used once each.
SHARED_MACROS = r"""
\definebadge{H1}{seriesA}
\definebadge{R1}{seriesB}
\begin{table}
  \caption{\lead{Every shared macro.} Risk \badge{R1} tests \badge{H1};
    \marker{seriesB} marks and \linekey{seriesA} joins the points.}
  \begin{tabular}{@{}llS[table-format=-1.2]S[table-format=3]@{}}
    \toprule
    & & \multicolumn{2}{c}{\spanhead{Fit}} \\
    \cmidrule(l){3-4}
    \colhead{Tag}{} & \colhead{Level}{} & \colhead{$\Delta T$}{\kelvin} & \colhead{$N$}{} \\
    \midrule
    \badgetarget{H1} & \level{low} & -0.25 & 120 \\
    \band \badgetarget{R1} & \level{medium} & 1.50 & 64 \\
    \keyrow H2 & \level{high} & -2.75 & 8 \\
    \bottomrule
  \end{tabular}
\end{table}
A cooling of \qty{-5}{\kelvin} in the {\color{seriesC}text} and \qty{3}{\milli\metre} in
\textbf{bold}, as \textsf{\qty{-2}{\kelvin} in the sans face}.
"""

ARTICLE = rf"""\documentclass[11pt]{{article}}
\usepackage{{laboratory}}
\title{{Shared macros}}
\author{{A. Student}}
\supervisor{{Dr A. Supervisor}}
\date{{28th September 2026}}
\source{{github.com/student/project}}
\begin{{document}}
\maketitle
{SHARED_MACROS}
\end{{document}}
"""

BEAMER = rf"""\documentclass[aspectratio=169, 11pt]{{beamer}}
\usetheme{{Laboratory}}
\title{{Shared macros}}
\author{{A. Student}}
\supervisor{{Dr A. Supervisor}}
\date{{28th September 2026}}
\source{{github.com/student/project}}
\begin{{document}}
\begin{{frame}}
  \titlepage
\end{{frame}}
\begin{{frame}}{{Tables and tags}}
{SHARED_MACROS}
\end{{frame}}
\end{{document}}
"""

# Every piece of page furniture laboratory.sty adds, used once each.
PAGE_FURNITURE = r"""
\section{Aim and hypotheses}
\begin{statement}{Aim}
  Measure the gravitational acceleration to one part in a thousand.
\end{statement}
\paragraph{Why it matters} The measurement tests the small-angle model.
\subsection{Hypotheses}
\begin{claims}
  \item[\badgetarget{H1}] The small-angle law holds at \qty{3}{\degree}.
\end{claims}
\begin{itemize}
  \item the period;
  \item the length.
\end{itemize}
\begin{milestones}
  \item MS1, apparatus verified: week 3.
\end{milestones}
\Cref{tab:risks} lists the risks to \badge{H1}.
\begin{table}[tbp]
  \caption{\lead{Risks to the measurement.} Each risk with its likelihood.}
  \label{tab:risks}
  \begin{threeparttable}
    \begin{tabular}{@{}ll@{}}
      \toprule
      \head{Risk} & \head{Likelihood} \\
      \midrule
      Gate misaligned\tnote{a} & \level{low} \\
      \bottomrule
    \end{tabular}
    \begin{tablenotes}
      \item[a] Checked every week.
    \end{tablenotes}
  \end{threeparttable}
\end{table}
"""


def furnished_document(document_class: str, chapter: str) -> str:
    return rf"""\documentclass[11pt]{{{document_class}}}
\usepackage{{laboratory}}
\kicker{{Project plan}}
\runninghead{{Pendulum}}
\title{{Page furniture}}
\author{{A. Student}}
\date{{28th September 2026}}
\begin{{document}}
\maketitle
\tableofcontents
{chapter}
{PAGE_FURNITURE}
\end{{document}}
"""


# Long words that a justified caption held to a narrow table hyphenates. A
# caption inside a threeparttable takes the table's width, so this is the
# narrowest a table caption gets.
LONG_CAPTION = (
    "Characteristically unrepresentative measurements of gravitational acceleration, "
    "interferometrically recalibrated against independently characterised photogates "
    "at seventeen pendulum lengths."
)

NARROW_TABLE = rf"""\documentclass[11pt]{{article}}
\usepackage{{laboratory}}
\title{{Captions}}
\begin{{document}}
\begin{{table}}
  \begin{{threeparttable}}
    \caption{{{LONG_CAPTION}}}
    \begin{{tabular}}{{@{{}}llll@{{}}}}
      \toprule
      \head{{Length}} & \head{{Period}} & \head{{Amplitude}} & \head{{Runs}} \\
      \midrule
      short & quick & small & five \\
      \bottomrule
    \end{{tabular}}
  \end{{threeparttable}}
\end{{table}}
\end{{document}}
"""

RUNNING_TEXT_QUANTITY = r"""\documentclass[11pt]{article}
\usepackage{laboratory}
\title{Quantities}
\begin{document}
The sample cooled by \qty{-5}{\kelvin} overnight.
\end{document}
"""


def write_project(folder: Path, source: str, packages: tuple[str, ...]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for package in packages:
        shutil.copyfile(ASSETS / package, folder / package)
    document = folder / "main.tex"
    document.write_text(source, encoding="utf-8")
    return document


def extract_text(pdf: Path) -> str:
    """The PDF's text line by line as set; without -raw, pdftotext rejoins hyphenated words."""
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    completed = subprocess.run(  # noqa: S603 - a fixed command found on PATH
        [pdftotext, "-raw", "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True,
        timeout=PDFTOTEXT_TIMEOUT_SECONDS,
        check=True,
    )
    return completed.stdout.decode("utf-8")


@pytest.mark.tex
@pytest.mark.parametrize(
    ("source", "packages"), [(ARTICLE, DOCUMENT_PACKAGES), (BEAMER, BEAMER_PACKAGES)]
)
def test_every_shared_macro_builds_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], source: str, packages: tuple[str, ...]
) -> None:
    document = write_project(tmp_path, source, packages)

    exit_code = build.main([str(document), "--engine", "lualatex"])

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "0 defects, 0 warnings" in output, output


@pytest.mark.tex
@pytest.mark.parametrize(
    "source",
    [
        furnished_document("article", ""),
        furnished_document("report", r"\chapter{Plan}"),
        furnished_document("report", r"\chapter{Plan}").replace(
            r"\usepackage{laboratory}", r"\usepackage[compact]{laboratory}"
        ),
    ],
    ids=["article", "report", "compact-report"],
)
def test_every_piece_of_page_furniture_builds_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], source: str
) -> None:
    document = write_project(tmp_path, source, DOCUMENT_PACKAGES)

    exit_code = build.main([str(document), "--engine", "lualatex"])

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "0 defects, 0 warnings" in output, output


@pytest.mark.tex
def test_a_long_table_caption_wraps_without_hyphenating(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write_project(tmp_path, NARROW_TABLE, DOCUMENT_PACKAGES)

    assert build.main([str(document), "--engine", "lualatex"]) == 0, capsys.readouterr().out

    words = extract_text(tmp_path / "build" / "main.pdf").split()
    split_words = [word for word in LONG_CAPTION.split() if word not in words]
    assert not split_words, words


@pytest.mark.tex
def test_a_negative_quantity_in_running_text_keeps_a_true_minus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write_project(tmp_path, RUNNING_TEXT_QUANTITY, DOCUMENT_PACKAGES)

    assert build.main([str(document), "--engine", "lualatex"]) == 0, capsys.readouterr().out

    text = extract_text(tmp_path / "build" / "main.pdf")
    assert f"{MINUS_SIGN}5" in text, text


@pytest.mark.tex
def test_reports_a_level_that_is_not_low_medium_or_high(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ARTICLE.replace(r"\level{high}", r"\level{severe}")
    document = write_project(tmp_path, source, DOCUMENT_PACKAGES)

    exit_code = build.main([str(document), "--engine", "lualatex"])

    assert exit_code == 1
    assert "severe" in capsys.readouterr().out


@pytest.mark.tex
def test_warns_of_a_badge_with_no_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ARTICLE.replace(r"\badgetarget{H1}", "H1")
    document = write_project(tmp_path, source, DOCUMENT_PACKAGES)

    exit_code = build.main([str(document), "--engine", "lualatex"])

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "badge.H1" in output, output


@pytest.mark.tex
def test_draws_a_top_rule_given_a_width_at_the_house_width(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ARTICLE.replace(r"\toprule", r"\toprule[2pt]")
    document = write_project(tmp_path, source, DOCUMENT_PACKAGES)

    exit_code = build.main([str(document), "--engine", "lualatex"])

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert r"\toprule[2pt]" in output, output
    assert "[2pt]" not in extract_text(tmp_path / "build" / "main.pdf")


LISTS_IN_BOXES = r"""\documentclass[11pt]{article}
\usepackage{laboratory}
\title{Lists}
\begin{document}
\begin{itemize}
  \item text\typeout{TEXT-LEFTMARGIN=\the\leftmargin}
\end{itemize}
\begin{statement}{Aim}
  \begin{itemize}
    \item statement\typeout{STATEMENT-LEFTMARGIN=\the\leftmargin}
  \end{itemize}
\end{statement}
\begin{tabular}{@{}p{50mm}@{}}
  \begin{itemize}
    \item cell\typeout{CELL-LEFTMARGIN=\the\leftmargin}
  \end{itemize}
\end{tabular}
\end{document}
"""


@pytest.mark.tex
def test_hangs_bullets_only_in_running_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write_project(tmp_path, LISTS_IN_BOXES, DOCUMENT_PACKAGES)

    assert build.main([str(document), "--engine", "lualatex"]) == 0, capsys.readouterr().out

    log = (tmp_path / "build" / "main.log").read_text(encoding="utf-8", errors="replace")
    assert "TEXT-LEFTMARGIN=0.0pt" in log
    for place in ("STATEMENT", "CELL"):
        margin = re.search(rf"{place}-LEFTMARGIN=([0-9.]+)pt", log)
        assert margin is not None, log
        assert float(margin.group(1)) > 0


RENDER_DPI = 72
MILLIMETRES_PER_INCH = 25.4
# Where the running head and its rule sit on a page: 34 mm to the text, less
# a 10 mm separation and the 14 pt head, with a few millimetres either side.
HEAD_BAND_MM = (15, 26)
# The darkest a pixel of grey 0.6 type gets once antialiased, with margin.
DARKEST_GREY = 100
PGM_HEADER = re.compile(rb"P5\s+(\d+)\s+(\d+)\s+\d+\s")


def darkest_in_head(pdf: Path, page: int) -> int:
    pdftoppm = shutil.which("pdftoppm")
    assert pdftoppm is not None
    stem = pdf.with_name("head")
    subprocess.run(  # noqa: S603 - a fixed command found on PATH
        [
            pdftoppm,
            "-gray",
            "-r",
            str(RENDER_DPI),
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            str(pdf),
            str(stem),
        ],
        capture_output=True,
        timeout=PDFTOTEXT_TIMEOUT_SECONDS,
        check=True,
    )
    image = stem.with_suffix(".pgm").read_bytes()
    header = PGM_HEADER.match(image)
    assert header is not None
    width = int(header.group(1))
    top, bottom = (round(mm / MILLIMETRES_PER_INCH * RENDER_DPI) for mm in HEAD_BAND_MM)
    band = image[header.end() + top * width : header.end() + bottom * width]
    return min(band)


@pytest.mark.tex
@pytest.mark.parametrize("running_head", ["", r"\runninghead{Pendulum}"], ids=["title", "short"])
def test_sets_the_running_head_in_grey(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], running_head: str
) -> None:
    source = rf"""\documentclass[11pt]{{article}}
\usepackage{{laboratory}}
{running_head}
\title{{Pendulum}}
\begin{{document}}
First page.
\clearpage
Second page.
\end{{document}}
"""
    document = write_project(tmp_path, source, DOCUMENT_PACKAGES)

    assert build.main([str(document), "--engine", "lualatex"]) == 0, capsys.readouterr().out

    assert darkest_in_head(tmp_path / "build" / "main.pdf", page=2) > DARKEST_GREY
