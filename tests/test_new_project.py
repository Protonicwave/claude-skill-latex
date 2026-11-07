import shutil
import subprocess
from pathlib import Path

import build
import lint
import pytest
from new_project import PROFILES, main, project_files

LATEXMK_TIMEOUT_SECONDS = 300
# REVTeX loads hyperref itself and then redefines \label, and its BibTeX
# style warns about its own control entry; the skeleton cannot avoid either.
CLASS_WARNING_PROFILES = frozenset({"paper"})


@pytest.mark.parametrize("profile", list(PROFILES))
def test_every_profile_has_a_main_document_and_its_assets(profile: str) -> None:
    files = project_files(profile)

    assert {"main.tex", "refs.bib", "latexmkrc", ".vscode/settings.json"} <= files.keys()
    assert "figures/pendulum.pdf" in files
    assert "figures/laboratory.mplstyle" in files


@pytest.mark.parametrize(("profile", "pdf_mode"), [("labreport", 4), ("paper", 1)])
def test_latexmkrc_selects_the_profile_engine(tmp_path: Path, profile: str, pdf_mode: int) -> None:
    assert main([profile, str(tmp_path)]) == 0

    latexmkrc = (tmp_path / "latexmkrc").read_text(encoding="utf-8")
    assert latexmkrc.startswith(f"$pdf_mode = {pdf_mode};")


def test_adds_a_project_to_a_folder_that_holds_other_files(tmp_path: Path) -> None:
    (tmp_path / "data.csv").write_text("length,period\n", encoding="utf-8")

    assert main(["notes", str(tmp_path)]) == 0
    assert (tmp_path / "data.csv").read_text(encoding="utf-8") == "length,period\n"
    assert (tmp_path / "main.tex").is_file()


def test_writes_nothing_when_a_file_it_needs_is_already_there(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "main.tex").write_text("mine\n", encoding="utf-8")

    assert main(["notes", str(tmp_path)]) == 2
    assert [path.name for path in tmp_path.iterdir()] == ["main.tex"]
    assert (tmp_path / "main.tex").read_text(encoding="utf-8") == "mine\n"
    assert "main.tex" in capsys.readouterr().err


def test_reports_a_folder_that_cannot_be_created(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = tmp_path / "notes.txt"
    blocker.write_text("", encoding="utf-8")

    assert main(["notes", str(blocker / "project")]) == 2
    assert "could not write" in capsys.readouterr().err


def test_rejects_an_unknown_profile(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["thesis", str(tmp_path)])

    assert exit_info.value.code == 2


@pytest.mark.tex
@pytest.mark.parametrize("profile", list(PROFILES))
def test_skeleton_builds_without_defects_and_lints_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], profile: str
) -> None:
    folder = tmp_path / "new project"
    assert main([profile, str(folder)]) == 0
    document = folder / "main.tex"

    exit_code = build.main([str(document), "--engine", PROFILES[profile].engine])

    output = capsys.readouterr().out
    assert exit_code == 0, output
    if profile not in CLASS_WARNING_PROFILES:
        assert "0 defects, 0 warnings" in output, output
    assert lint.lint(document).findings == ()


@pytest.mark.tex
def test_latexmk_alone_finds_the_bibliography_through_the_latexmkrc(tmp_path: Path) -> None:
    assert main(["labreport", str(tmp_path)]) == 0
    latexmk = shutil.which("latexmk")
    assert latexmk is not None

    # This is how an editor builds: latexmk with no options, reading only the
    # latexmkrc. Output goes nowhere rather than to a pipe, which an engine
    # outliving a timeout would hold open.
    completed = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [latexmk, "-interaction=nonstopmode", "-halt-on-error"],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=LATEXMK_TIMEOUT_SECONDS,
        check=False,
    )

    assert completed.returncode == 0
    bibtex_log = (tmp_path / "build" / "main.blg").read_text(encoding="utf-8", errors="replace")
    assert "refs.bib" in bibtex_log
    assert "couldn't open" not in bibtex_log
