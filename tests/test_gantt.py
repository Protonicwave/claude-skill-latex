"""The plan profile's figures/gantt.py, run as a student runs it in a new project."""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import matplotlib.pyplot as plt
import pytest
from new_project import main

# The script imports matplotlib, and drawing starts LuaLaTeX through the pgf backend.
SCRIPT_TIMEOUT_SECONDS = 300
PDFTOTEXT_TIMEOUT_SECONDS = 60
POINTS_PER_INCH = 72


@pytest.fixture
def project(tmp_path: Path) -> Path:
    assert main(["plan", str(tmp_path)]) == 0
    return tmp_path


def edit_tables(project: Path, old: str, new: str) -> None:
    script = project / "figures" / "gantt.py"
    source = script.read_text(encoding="utf-8")
    assert source.count(old) == 1, f"expected {old!r} once in the tables"
    script.write_text(source.replace(old, new), encoding="utf-8")


def load_script(project: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The project's gantt.py as a module, importing the helper beside it."""
    folder = project / "figures"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location("gantt", folder / "gantt.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Its dataclasses look their module up while they are built.
    monkeypatch.setitem(sys.modules, "gantt", module)
    spec.loader.exec_module(module)
    return module


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


def pdftotext(chart: Path, *options: str) -> str:
    command = shutil.which("pdftotext")
    assert command is not None
    return subprocess.run(  # noqa: S603 - a fixed command found on PATH
        [command, "-enc", "UTF-8", *options, str(chart), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=PDFTOTEXT_TIMEOUT_SECONDS,
        check=True,
    ).stdout


@pytest.mark.tex
def test_redraws_the_chart_from_the_edited_tables(project: Path) -> None:
    chart = project / "figures" / "gantt.pdf"
    chart.unlink()
    edit_tables(project, '"Draft"', '"Write the report"')

    completed = run_script(project)

    assert completed.returncode == 0, completed.stderr
    assert "Write the report" in pdftotext(chart)


@pytest.mark.parametrize("week", [12, 17, 19, 20])
def test_keeps_a_late_milestone_label_inside_the_chart(
    project: Path, monkeypatch: pytest.MonkeyPatch, week: int
) -> None:
    edit_tables(project, 'Mark("MS3", 15', f'Mark("MS3", {week}')
    gantt = load_script(project, monkeypatch)
    # The script draws through pyplot; Agg needs no display or TeX.
    plt.switch_backend("agg")

    with plt.style.context(project / "figures" / "laboratory.mplstyle"):
        figure = gantt.draw()
        figure.draw_without_rendering()

    (axes,) = figure.axes
    labels = [text for text in axes.texts if text.get_text().startswith("MS")]
    assert len(labels) == len(gantt.MILESTONES)
    chart_right_px = axes.get_window_extent().x1
    gap_px = gantt.MARK_LABEL_GAP_PT / POINTS_PER_INCH * figure.dpi
    for label in labels:
        box = label.get_window_extent()
        assert box.x1 <= chart_right_px
        if label.get_horizontalalignment() == "right":
            # Turned back only because it could not fit to the right of its mark.
            mark_px = axes.transData.transform(label.xy)[0]
            assert mark_px + gap_px + box.width > chart_right_px
    plt.close(figure)
