import shutil
import subprocess
from pathlib import Path

import build
import pytest
from new_project import ASSETS, DOCUMENT_PACKAGES

PDFTOTEXT_TIMEOUT_SECONDS = 60
MINUS_SIGN = "\N{MINUS SIGN}"

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
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    completed = subprocess.run(  # noqa: S603 - a fixed command found on PATH
        [pdftotext, "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True,
        timeout=PDFTOTEXT_TIMEOUT_SECONDS,
        check=True,
    )
    return completed.stdout.decode("utf-8")


@pytest.mark.tex
def test_a_negative_quantity_in_running_text_keeps_a_true_minus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = write_project(tmp_path, RUNNING_TEXT_QUANTITY, DOCUMENT_PACKAGES)

    assert build.main([str(document), "--engine", "lualatex"]) == 0, capsys.readouterr().out

    text = extract_text(tmp_path / "build" / "main.pdf")
    assert f"{MINUS_SIGN}5" in text, text
