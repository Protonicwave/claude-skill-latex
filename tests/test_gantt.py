"""The plan profile's figures/gantt.py, run as a student runs it in a new project."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from new_project import main

# The script imports matplotlib, and drawing starts LuaLaTeX through the pgf backend.
SCRIPT_TIMEOUT_SECONDS = 300


@pytest.fixture
def project(tmp_path: Path) -> Path:
    assert main(["plan", str(tmp_path)]) == 0
    return tmp_path


def edit_tables(project: Path, old: str, new: str) -> None:
    script = project / "figures" / "gantt.py"
    source = script.read_text(encoding="utf-8")
    assert source.count(old) == 1, f"expected {old!r} once in the tables"
    script.write_text(source.replace(old, new), encoding="utf-8")


def run_script(project: Path) -> subprocess.CompletedProcess[str]:
    # From the project folder, as the script's docstring tells a student to.
    return subprocess.run(  # noqa: S603 - the running interpreter and a fixed script path
        [sys.executable, str(Path("figures") / "gantt.py")],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=False,
    )


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('Task("2.2", "Fit', 'Task("2.1", "Fit', "task code '2.1' appears twice"),
        ('"Draft", 16, 18', '"Draft", 18, 16', "task 5.1 ends in week 16"),
        ('Mark("MS2", 7, "2.2"', 'Mark("MS2", 7, "2.9"', "MS2 sits on task '2.9'"),
        ('Mark("R2"', 'Mark("R1"', "mark code 'R1' appears twice"),
        (
            '"Revision and viva", 18, 20',
            '"Revision and viva", 18, 22',
            "task 5.2 runs from week 18 to 22, outside",
        ),
        ('Mark("MS1", 3', 'Mark("MS1", -1', "MS1 falls in week -1"),
        ("(10, 13, ", "(13, 10, ", "break 'vacation' ends in week 10"),
        ("(10, 13, ", "(10, 23, ", "break 'vacation' runs from week 10 to 23, outside"),
        ("done_until_week=5)", "done_until_week=5.5)", "task 2.1 is done to week 5.5"),
        (
            'lab.INK, is_package=True),\n    Task("1.1"',
            'lab.INK, done_until_week=3, is_package=True),\n    Task("1.1"',
            "task 1 is a work package",
        ),
    ],
    ids=[
        "duplicate-code",
        "ends-before-start",
        "unknown-task",
        "duplicate-mark",
        "task-after-chart",
        "mark-before-chart",
        "break-ends-before-start",
        "break-after-chart",
        "done-after-status",
        "done-on-package",
    ],
)
def test_rejects_a_table_it_cannot_draw_and_leaves_the_chart(
    project: Path, old: str, new: str, message: str
) -> None:
    chart = project / "figures" / "gantt.pdf"
    before = chart.read_bytes()
    edit_tables(project, old, new)

    completed = run_script(project)

    assert completed.returncode != 0
    assert f"ValueError: {message}" in completed.stderr
    assert chart.read_bytes() == before


@pytest.mark.tex
def test_redraws_the_chart_from_the_edited_tables(project: Path) -> None:
    chart = project / "figures" / "gantt.pdf"
    chart.unlink()
    edit_tables(project, '"Draft"', '"Write the report"')

    completed = run_script(project)

    assert completed.returncode == 0, completed.stderr
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    text = subprocess.run(  # noqa: S603 - a fixed command found on PATH
        [pdftotext, "-enc", "UTF-8", str(chart), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=True,
    ).stdout
    assert "Write the report" in text
