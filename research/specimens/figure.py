"""Draw the specimen figure in one direction's fonts and colours.

The figure is typeset by LuaLaTeX through matplotlib's pgf backend, so its text
uses the same faces as the document, and it is drawn at the full text width so
it is included at scale 1 and its type stays at the size set here.

Usage:
    python figure.py DIRECTION DATA.csv OUTPUT.pdf
"""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

MILLIMETRES_PER_INCH = 25.4
FIGURE_FONT_SIZE_PT = 9
ASPECT_RATIO = 0.40
CRITICAL_TEMPERATURE = 2 / math.log(1 + math.sqrt(2))


@dataclass(frozen=True, slots=True)
class Direction:
    text_width_mm: float
    font_family: str
    preamble: str
    data_colour: str
    theory_colour: str
    guide_colour: str


PLEX_MONO = r"\setmonofont{IBMPlexMono}[Extension=.otf,UprightFont=*-Regular,Scale=MatchLowercase]"

DIRECTIONS = {
    "journal": Direction(
        text_width_mm=122,
        font_family="serif",
        preamble="\n".join(
            [
                r"\usepackage{fontspec}",
                r"\usepackage{unicode-math}",
                r"\setmainfont{STIXTwoText}[Extension=.otf,UprightFont=*-Regular,"
                r"ItalicFont=*-Italic]",
                r"\setmathfont{STIXTwoMath-Regular.otf}",
                PLEX_MONO,
            ]
        ),
        data_colour="#111111",
        theory_colour="#8C8C8C",
        guide_colour="#8C8C8C",
    ),
    "rubric": Direction(
        text_width_mm=130,
        font_family="serif",
        preamble="\n".join(
            [
                r"\usepackage{fontspec}",
                r"\usepackage{unicode-math}",
                r"\setmainfont{texgyrepagella}[Extension=.otf,UprightFont=*-regular,"
                r"ItalicFont=*-italic,Numbers=Lining]",
                r"\setmathfont{Euler-Math.otf}",
                PLEX_MONO,
            ]
        ),
        data_colour="#A3301F",
        theory_colour="#1A1A1A",
        guide_colour="#8C8C8C",
    ),
    "laboratory": Direction(
        text_width_mm=175,
        font_family="sans-serif",
        preamble="\n".join(
            [
                r"\usepackage{fontspec}",
                r"\usepackage{unicode-math}",
                r"\setmainfont{Erewhon}[Extension=.otf,UprightFont=*-Regular,"
                r"ItalicFont=*-Italic,Scale=0.95]",
                r"\setsansfont{SourceSans3}[Extension=.otf,UprightFont=*-Regular,"
                r"ItalicFont=*-RegularIt]",
                r"\setmathfont{Erewhon-Math.otf}[Scale=0.95]",
                # The same tightened maths slash as specimen-laboratory.sty.
                r"\AtBeginDocument{\Umathcharnumdef\erewhonslash=\Umathcodenum`\/\relax"
                r"\begingroup\lccode`\~=`\/\lowercase{\endgroup\def~}"
                r"{\mkern-2mu\erewhonslash\mkern-2mu}\mathcode`\/=" + '"8000\\relax}',
                PLEX_MONO,
            ]
        ),
        data_colour="#1F4A73",
        theory_colour="#1A1A1A",
        guide_colour="#999999",
    ),
}


@dataclass(frozen=True, slots=True)
class Measurements:
    temperature: list[float]
    abs_m: list[float]
    abs_m_err: list[float]
    chi: list[float]
    chi_err: list[float]


def read_measurements(path: Path) -> Measurements:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"expected data rows in {path}, found none")

    def column(name: str) -> list[float]:
        return [float(row[name]) for row in rows]

    return Measurements(
        column("temperature"),
        column("abs_m"),
        column("abs_m_err"),
        column("chi"),
        column("chi_err"),
    )


def exact_magnetisation(temperature: float) -> float:
    """Yang's spontaneous magnetisation of the infinite lattice, zero above T_c."""
    if temperature >= CRITICAL_TEMPERATURE:
        return 0.0
    return float((1 - math.sinh(2 / temperature) ** -4) ** 0.125)


def configure(direction: Direction) -> None:
    mpl.rcParams.update(
        {
            "pgf.texsystem": "lualatex",
            "pgf.rcfonts": False,
            "pgf.preamble": direction.preamble,
            "font.family": direction.font_family,
            "font.size": FIGURE_FONT_SIZE_PT,
            "axes.labelsize": FIGURE_FONT_SIZE_PT,
            "xtick.labelsize": FIGURE_FONT_SIZE_PT,
            "ytick.labelsize": FIGURE_FONT_SIZE_PT,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "axes.unicode_minus": True,
        }
    )


def label_panel(axes: Axes, label: str) -> None:
    """Label above the axes, where it cannot collide with data."""
    axes.set_title(label, loc="left", fontsize=FIGURE_FONT_SIZE_PT, pad=4)


def plot_points(
    axes: Axes, x: list[float], y: list[float], error: list[float], colour: str
) -> None:
    axes.errorbar(x, y, yerr=error, fmt="o", ms=3.2, color=colour, elinewidth=0.8)


def draw(direction: Direction, data: Measurements, output: Path) -> None:
    configure(direction)
    width_in = direction.text_width_mm / MILLIMETRES_PER_INCH
    figure, (left, right) = plt.subplots(
        1, 2, figsize=(width_in, width_in * ASPECT_RATIO), layout="constrained"
    )
    grid = np.linspace(1.5, 3.5, 801)
    left.plot(grid, [exact_magnetisation(t) for t in grid], color=direction.theory_colour, lw=1.0)
    plot_points(left, data.temperature, data.abs_m, data.abs_m_err, direction.data_colour)
    left.set_ylabel(r"$\langle |m| \rangle$")
    left.set_ylim(0, 1.05)
    plot_points(right, data.temperature, data.chi, data.chi_err, direction.data_colour)
    right.set_ylabel(r"$\chi$")
    right.set_ylim(0, None)

    for axes, label in ((left, "(a)"), (right, "(b)")):
        axes.axvline(
            CRITICAL_TEMPERATURE, color=direction.guide_colour, lw=0.7, ls=(0, (3, 3)), zorder=0
        )
        axes.set_xlabel(r"$T$ ($J/k_\mathrm{B}$)")
        axes.set_xlim(1.5, 3.5)
        label_panel(axes, label)

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, backend="pgf")
    plt.close(figure)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in DIRECTIONS:  # noqa: PLR2004
        sys.exit(f"usage: figure.py {{{'|'.join(DIRECTIONS)}}} DATA.csv OUTPUT.pdf")
    draw(DIRECTIONS[sys.argv[1]], read_measurements(Path(sys.argv[2])), Path(sys.argv[3]))
