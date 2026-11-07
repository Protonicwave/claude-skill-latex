from pathlib import Path

import pytest
from build import main as build_main
from render import MAX_PAGES, main, parse_pages

THREE_PAGES = r"""\documentclass{article}
\begin{document}
First page.\newpage
Second page.\newpage
Third page.
\end{document}
"""


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (None, [1, 2, 3, 4, 5]),
        ("2", [2]),
        ("1,3-4", [1, 3, 4]),
        ("4-5, 1", [1, 4, 5]),
        ("2-4,3,3-5", [2, 3, 4, 5]),
        ("5-5", [5]),
    ],
)
def test_reads_pages_and_ranges_in_order_without_repeats(
    spec: str | None, expected: list[int]
) -> None:
    assert parse_pages(spec, 5) == expected


@pytest.mark.parametrize("spec", ["", "0", "6", "4-6", "3-1", "a", "1,,2", "1-", "-2", "1.5"])
def test_rejects_malformed_or_out_of_range_pages(spec: str) -> None:
    with pytest.raises(ValueError, match="expected"):
        parse_pages(spec, 5)


def test_refuses_more_pages_than_the_limit_without_a_selection() -> None:
    with pytest.raises(ValueError, match="--pages"):
        parse_pages(None, MAX_PAGES + 1)


def test_accepts_a_selection_from_a_document_longer_than_the_limit() -> None:
    assert parse_pages("1,60", MAX_PAGES + 30) == [1, 60]


@pytest.fixture(scope="module")
def three_page_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    document = tmp_path_factory.mktemp("render") / "pages.tex"
    document.write_text(THREE_PAGES, encoding="utf-8")
    assert build_main([str(document), "--engine", "pdflatex"]) == 0
    return document.parent / "build" / "pages.pdf"


@pytest.mark.tex
def test_writes_one_png_per_requested_page(three_page_pdf: Path, tmp_path: Path) -> None:
    exit_code = main([str(three_page_pdf), "--pages", "1,3", "--outdir", str(tmp_path)])

    assert exit_code == 0
    assert sorted(path.name for path in tmp_path.iterdir()) == ["pages-1.png", "pages-3.png"]
    assert (tmp_path / "pages-1.png").read_bytes().startswith(b"\x89PNG")


@pytest.mark.tex
def test_renders_every_page_beside_the_pdf_by_default(three_page_pdf: Path) -> None:
    assert main([str(three_page_pdf)]) == 0

    rendered = sorted(path.name for path in (three_page_pdf.parent / "pages").iterdir())
    assert rendered == ["pages-1.png", "pages-2.png", "pages-3.png"]


@pytest.mark.tex
def test_rejects_a_page_past_the_end(three_page_pdf: Path, tmp_path: Path) -> None:
    assert main([str(three_page_pdf), "--pages", "4", "--outdir", str(tmp_path)]) == 2
    assert not list(tmp_path.iterdir())


@pytest.mark.tex
def test_reports_a_file_that_is_not_a_valid_pdf_as_a_tool_failure(tmp_path: Path) -> None:
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"not a pdf")

    assert main([str(broken)]) == 1


def test_rejects_a_path_that_is_not_a_pdf(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    image.write_bytes(b"\x89PNG")

    assert main([str(image)]) == 2


def test_rejects_a_resolution_outside_the_range(tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF-1.5")

    with pytest.raises(SystemExit):
        main([str(pdf), "--dpi", "1200"])
