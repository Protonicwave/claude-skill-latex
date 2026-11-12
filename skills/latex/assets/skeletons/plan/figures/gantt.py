"""Draw the plan's Gantt chart, gantt.pdf, from the tables at the top of this file.

Edit the tables to match the plan, then run, from any folder:

    python figures/gantt.py

Weeks count from the start of the project; a week may be fractional, so a
task can end mid-week. A task that tests a hypothesis takes the colour
\\definebadge gives that hypothesis in main.tex, so the chart, the risk table
and the figures share one key. The script reads laboratory.mplstyle and the
figure helper, laboratory.py, from its own folder.

Raises ValueError, before drawing anything, for two tasks with one code, a task
that does not end after it starts, or a milestone or risk on a task that is not
in TASKS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import laboratory as lab
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


@dataclass(frozen=True, slots=True)
class Task:
    code: str
    name: str
    start_week: float
    end_week: float
    colour: str
    # The work is done up to this week; 0 means none of it is.
    done_until_week: float = 0
    # A work package is drawn as a heading row over the tasks that follow it.
    is_package: bool = False


@dataclass(frozen=True, slots=True)
class Mark:
    code: str
    week: float
    # The code of the task whose row the mark sits on.
    task: str
    label: str = ""


WEEKS = 20
STATUS_WEEK = 5
# First week, last week and name of each break, such as a vacation.
BREAKS = ((11, 13, "vacation"),)
TASKS = (
    Task("1", "Apparatus and timing", 1, 3, lab.INK, is_package=True),
    Task("1.1", "Build, align, calibrate gate", 1, 3, lab.GREY, done_until_week=3),
    Task("2", "Small-angle law", 3, 7, lab.PRUSSIAN, is_package=True),
    Task("2.1", "Nine lengths at 3°", 3, 5.5, lab.PRUSSIAN, done_until_week=5),
    Task("2.2", "Fit, residuals, verdict on H1", 5.5, 7, lab.PRUSSIAN),
    Task("3", "Amplitude correction", 7, 15, lab.TERRACOTTA, is_package=True),
    Task("3.1", "Runs from 2° to 30°", 7, 10, lab.TERRACOTTA),
    Task("3.2", "Model comparison, verdict on H2", 13, 15, lab.TERRACOTTA),
    Task("4", "Length offset (H3)", 15, 16, lab.GREY, is_package=True),
    Task("5", "Report and viva", 16, 20, lab.INK, is_package=True),
    Task("5.1", "Draft", 16, 18, lab.GREY),
    Task("5.2", "Revision and viva", 18, 20, lab.GREY),
)
MILESTONES = (
    Mark("MS1", 3, "1.1", "Apparatus verified"),
    Mark("MS2", 7, "2.2", "Verdict on H1"),
    Mark("MS3", 15, "3.2", "Verdict on H2"),
    Mark("MS4", 20, "5.2", "Report submitted"),
)
# The weeks the triggers of the plan's risk table fall in.
RISKS = (Mark("R1", 6, "2.2"), Mark("R2", 9, "3.1"), Mark("R3", 14, "3.2"))

WIDTH_MM = 150
# Heading and week numbers, then one row per task, so the rows keep their
# height however many tasks there are.
HEAD_MM = 12
ROW_MM = 5.5
BAR_HEIGHT_ROWS = 0.56
PACKAGE_LINE_WIDTH_PT = 2.4
SMALL_TYPE_PT = 8
LABEL_GAP_PT = 6
PLANNED_TINT = 0.72
PACKAGE_ROW_TINT = 0.94
WEEK_RULE_TINT = 0.88
BREAK_HATCH_TINT = 0.55


def check_tables(tasks: tuple[Task, ...], marks: tuple[Mark, ...]) -> None:
    """Raise ValueError naming the first entry the chart could not draw faithfully."""
    codes: set[str] = set()
    for task in tasks:
        if task.code in codes:
            raise ValueError(f"task code {task.code!r} appears twice in TASKS")
        codes.add(task.code)
        if task.end_week <= task.start_week:
            raise ValueError(
                f"task {task.code} ends in week {task.end_week}, "
                f"expected after its start in week {task.start_week}"
            )
    for mark in marks:
        if mark.task not in codes:
            raise ValueError(f"{mark.code} sits on task {mark.task!r}, which is not in TASKS")


def draw_rows(axes: Axes) -> None:
    for row, task in enumerate(TASKS):
        if task.is_package:
            band = Rectangle(
                (0, row - 0.5),
                WEEKS + 1,
                1,
                color=lab.tint(lab.INK, PACKAGE_ROW_TINT),
                lw=0,
                zorder=0,
            )
            axes.add_patch(band)
            axes.plot(
                [task.start_week, task.end_week],
                [row, row],
                color=task.colour,
                lw=PACKAGE_LINE_WIDTH_PT,
                solid_capstyle="butt",
                zorder=2,
            )
            continue
        bottom = row - BAR_HEIGHT_ROWS / 2
        planned_weeks = task.end_week - task.start_week
        planned = lab.tint(task.colour, PLANNED_TINT)
        axes.add_patch(
            Rectangle(
                (task.start_week, bottom),
                planned_weeks,
                BAR_HEIGHT_ROWS,
                color=planned,
                lw=0,
                zorder=2,
            )
        )
        done_weeks = min(task.done_until_week, task.end_week) - task.start_week
        if done_weeks > 0:
            axes.add_patch(
                Rectangle(
                    (task.start_week, bottom),
                    done_weeks,
                    BAR_HEIGHT_ROWS,
                    color=task.colour,
                    lw=0,
                    zorder=3,
                )
            )


def draw_calendar(axes: Axes) -> None:
    top = len(TASKS) - 0.35
    for first, last, name in BREAKS:
        hatch = Rectangle(
            (first, -0.5),
            last - first,
            len(TASKS),
            facecolor="none",
            edgecolor=lab.tint(lab.GREY, BREAK_HATCH_TINT),
            hatch="////",
            lw=0,
            zorder=1,
        )
        axes.add_patch(hatch)
        axes.text((first + last) / 2, top, name, ha="center", va="top", color=lab.GREY)
    for week in range(1, WEEKS + 1):
        axes.axvline(week - 0.5, color=lab.tint(lab.INK, WEEK_RULE_TINT), lw=0.4, zorder=0.5)
    axes.axvline(STATUS_WEEK, color=lab.INK, lw=0.8, zorder=4)
    axes.annotate(
        f"status, week {STATUS_WEEK}",
        (STATUS_WEEK, top),
        xytext=(4, 0),
        textcoords="offset points",
        va="top",
        color=lab.INK,
    )


def draw_marks(axes: Axes) -> None:
    rows = {task.code: row for row, task in enumerate(TASKS)}
    for mark in MILESTONES:
        row = rows[mark.task]
        axes.plot(
            [mark.week],
            [row],
            marker="D",
            color=lab.INK,
            markersize=5,
            markeredgecolor="white",
            markeredgewidth=0.5,
            zorder=5,
        )
        # The last week's label would run off the chart, so it sits to the left.
        is_last = mark.week >= WEEKS
        axes.annotate(
            f"{mark.code} {mark.label}",
            (mark.week, row),
            xytext=(-7 if is_last else 7, 0),
            textcoords="offset points",
            ha="right" if is_last else "left",
            va="center",
            fontsize=SMALL_TYPE_PT,
            color=lab.INK,
            zorder=6,
        )
    for mark in RISKS:
        row = rows[mark.task]
        axes.plot(
            [mark.week],
            [row],
            marker="^",
            color="white",
            markersize=5.5,
            markeredgecolor=lab.TERRACOTTA,
            markeredgewidth=0.9,
            zorder=5,
        )
        axes.annotate(
            mark.code,
            (mark.week, row),
            xytext=(-6, 0),
            textcoords="offset points",
            ha="right",
            va="center",
            fontsize=SMALL_TYPE_PT,
            color=lab.TERRACOTTA,
            family="sans-serif",
            weight="bold",
        )


def label_axes(axes: Axes) -> None:
    axes.set_ylim(len(TASKS) + 0.3, -0.6)
    axes.set_xlim(0.5, WEEKS + 0.5)
    axes.set_yticks(range(len(TASKS)), [f"{task.code}  {task.name}" for task in TASKS])
    for label, task in zip(axes.get_yticklabels(), TASKS, strict=True):
        label.set_horizontalalignment("left")
        if task.is_package:
            label.set_fontweight("bold")
    axes.set_xticks(range(1, WEEKS + 1))
    axes.xaxis.tick_top()
    axes.tick_params(axis="x", length=0, labelsize=SMALL_TYPE_PT, colors=lab.GREY)
    axes.set_xlabel("week", color=lab.GREY, fontsize=SMALL_TYPE_PT)
    axes.xaxis.set_label_position("top")
    for spine in axes.spines.values():
        spine.set_visible(False)


def hang_task_names(figure: Figure, axes: Axes) -> None:
    """Set the left-aligned task names clear of the chart, however long the longest is."""
    figure.draw_without_rendering()
    widest_px = max(label.get_window_extent().width for label in axes.get_yticklabels())
    widest_pt = widest_px / figure.dpi * lab.POINTS_PER_INCH
    axes.tick_params(axis="y", length=0, pad=widest_pt + LABEL_GAP_PT)


def main() -> None:
    check_tables(TASKS, MILESTONES + RISKS)
    # The pgf canvas sets the labels in the document's faces and measures them as LuaLaTeX does.
    mpl.use("pgf")
    folder = Path(__file__).resolve().parent
    height_mm = HEAD_MM + ROW_MM * len(TASKS)
    size_in = (WIDTH_MM / lab.MILLIMETRES_PER_INCH, height_mm / lab.MILLIMETRES_PER_INCH)
    with plt.style.context(folder / "laboratory.mplstyle"):
        figure, axes = plt.subplots(figsize=size_in)
        draw_rows(axes)
        draw_calendar(axes)
        draw_marks(axes)
        label_axes(axes)
        hang_task_names(figure, axes)
        figure.savefig(folder / "gantt.pdf")
        plt.close(figure)


if __name__ == "__main__":
    main()
