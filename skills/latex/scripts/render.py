"""Render PDF pages to PNG so they can be inspected by eye.

Usage:
    python render.py PDF [--pages SPEC] [--dpi N] [--outdir DIR]

SPEC lists 1-based pages and ranges, such as `1,3-5`. Without it every page
is rendered, up to MAX_PAGES; a longer document needs SPEC. Each page is
written to DIR/<pdf stem>-<page>.png (DIR defaults to `pages` beside the PDF)
and its path printed.

Exit code 0 means every requested page was written, 1 means pdfinfo or
pdftoppm failed, 2 means a bad argument, an unusable output folder or a tool
missing from PATH.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

MAX_PAGES = 40
DEFAULT_DPI = 110
MIN_DPI = 36
MAX_DPI = 300
TOOL_TIMEOUT_SECONDS = 60
PAGE_COUNT = re.compile(r"^Pages:\s+(\d+)\s*$", re.MULTILINE)
PAGE_RANGE = re.compile(r"^(\d+)(?:-(\d+))?$")


def parse_pages(spec: str | None, page_count: int) -> list[int]:
    """Turn a page list such as `1,3-5` into sorted, distinct page numbers.

    Raises ValueError for malformed parts, reversed ranges, pages outside the
    document, and more than MAX_PAGES pages.
    """
    if spec is None:
        pages = set(range(1, page_count + 1))
    else:
        pages = set()
        for part in spec.split(","):
            pages |= _parse_part(part.strip(), page_count)
    if len(pages) > MAX_PAGES:
        message = f"expected at most {MAX_PAGES} pages, got {len(pages)}; choose some with --pages"
        raise ValueError(message)
    return sorted(pages)


def _parse_part(part: str, page_count: int) -> set[int]:
    match = PAGE_RANGE.match(part)
    if match is None:
        raise ValueError(f"expected a page or a range such as 3-5, got {part!r}")
    first = int(match.group(1))
    last = int(match.group(2) or first)
    if first > last:
        raise ValueError(f"expected a range that runs forwards, got {part!r}")
    if first < 1 or last > page_count:
        raise ValueError(f"expected pages from 1 to {page_count}, got {part!r}")
    return set(range(first, last + 1))


def count_pages(pdfinfo: str, pdf: Path) -> int:
    result = subprocess.run(
        [pdfinfo, str(pdf)],
        capture_output=True,
        check=True,
        text=True,
        errors="replace",
        timeout=TOOL_TIMEOUT_SECONDS,
    )
    match = PAGE_COUNT.search(result.stdout)
    if match is None:
        raise subprocess.SubprocessError(f"pdfinfo reported no page count for {pdf}")
    return int(match.group(1))


def render_page(pdftoppm: str, pdf: Path, page: int, dpi: int, outdir: Path) -> Path:
    # pdftoppm appends ".png" to the root it is given, so a stem holding dots
    # stays whole, which Path.with_suffix would not keep.
    root = f"{pdf.stem}-{page}"
    subprocess.run(
        [
            pdftoppm,
            "-png",
            "-r",
            str(dpi),
            "-f",
            str(page),
            "-l",
            str(page),
            # Names the file exactly, instead of appending a zero-padded page number.
            "-singlefile",
            str(pdf),
            str(outdir / root),
        ],
        capture_output=True,
        check=True,
        text=True,
        errors="replace",
        timeout=TOOL_TIMEOUT_SECONDS,
    )
    return outdir / f"{root}.png"


def _dpi(text: str) -> int:
    value = int(text)
    if not MIN_DPI <= value <= MAX_DPI:
        raise argparse.ArgumentTypeError(f"expected {MIN_DPI} to {MAX_DPI}, got {value}")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", help="pages and ranges such as 1,3-5 (default: all)")
    parser.add_argument("--dpi", type=_dpi, default=DEFAULT_DPI)
    parser.add_argument("--outdir", type=Path, help="default: pages beside the PDF")
    args = parser.parse_args(argv)

    pdf = args.pdf.resolve()
    if pdf.suffix.lower() != ".pdf" or not pdf.is_file():
        print(f"expected an existing .pdf file, got {args.pdf}", file=sys.stderr)
        return 2
    pdfinfo, pdftoppm = shutil.which("pdfinfo"), shutil.which("pdftoppm")
    if pdfinfo is None or pdftoppm is None:
        print("pdfinfo and pdftoppm must be on PATH; MiKTeX and poppler ship both", file=sys.stderr)
        return 2
    try:
        page_count = count_pages(pdfinfo, pdf)
        pages = parse_pages(args.pages, page_count)
    except (ValueError, subprocess.SubprocessError) as error:
        return _report_failure(error)
    outdir = args.outdir or pdf.parent / "pages"
    try:
        outdir.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"cannot use {outdir} as the output folder: {error.strerror}", file=sys.stderr)
        return 2
    for page in pages:
        try:
            print(render_page(pdftoppm, pdf, page, args.dpi, outdir))
        except subprocess.SubprocessError as error:
            return _report_failure(error)
    return 0


def _report_failure(error: ValueError | subprocess.SubprocessError) -> int:
    """Print why the run stopped and return its exit code: 2 for a bad argument, 1 otherwise."""
    if isinstance(error, subprocess.CalledProcessError):
        print(
            f"{error.cmd[0]} failed with status {error.returncode}: {error.stderr}", file=sys.stderr
        )
    elif isinstance(error, subprocess.TimeoutExpired):
        print(f"{error.cmd[0]} took longer than {error.timeout:g} s", file=sys.stderr)
    else:
        print(error, file=sys.stderr)
    return 2 if isinstance(error, ValueError) else 1


if __name__ == "__main__":
    sys.exit(main())
