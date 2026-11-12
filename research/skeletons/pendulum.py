"""Draw the pendulum figure the profile skeletons include, once for each medium.

Each figure uses the house mplstyle with its medium's overlay, which sets the
size the skeleton includes it at, so its type matches the page around it, and
the figure helper, laboratory.py, for its ticks, axes, labels and points. The
data are the skeletons' example measurements: the tables there quote the same
numbers.

Usage:
    python research/skeletons/pendulum.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ASSETS = Path(__file__).resolve().parents[2] / "skills" / "latex" / "assets"
# The helper is an asset copied into each project, not an installed package.
sys.path.insert(0, str(ASSETS / "mplstyle"))
import laboratory as lab  # noqa: E402

LENGTHS_M = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
PERIODS_S = (0.8983, 1.0980, 1.2692, 1.4170, 1.5548, 1.6787, 1.7937, 1.9042, 2.0057)
PERIOD_ERROR_MS = 1.0
MILLISECONDS_PER_SECOND = 1000
FIT_BAND_TINT = 0.86
# The overlays each medium adds to laboratory.mplstyle. A journal column stacks
# the panels, and the journal's own design runs y labels up the axis.
MEDIA = {"document": (), "journal": ("journal",), "slides": ("slides",), "poster": ("poster",)}


def fitted_coefficient() -> tuple[float, float]:
    """Least-squares a in T = a sqrt(L), every period weighted equally, with its standard error."""
    weighted = sum(
        period * math.sqrt(length) for period, length in zip(PERIODS_S, LENGTHS_M, strict=True)
    )
    total_length_m = sum(LENGTHS_M)
    error = PERIOD_ERROR_MS / MILLISECONDS_PER_SECOND / math.sqrt(total_length_m)
    return weighted / total_length_m, error


def draw(medium: str, overlays: tuple[str, ...]) -> Path:
    styles = [ASSETS / "mplstyle" / f"{name}.mplstyle" for name in ("laboratory", *overlays)]
    coefficient, coefficient_error = fitted_coefficient()
    lengths = np.array(LENGTHS_M)
    residuals_ms = (np.array(PERIODS_S) - coefficient * np.sqrt(lengths)) * MILLISECONDS_PER_SECOND
    grid = np.linspace(0.15, 1.05, 200)
    band_ms = coefficient_error * np.sqrt(grid) * MILLISECONDS_PER_SECOND
    is_journal = medium == "journal"
    with plt.style.context(styles):
        figure, (period, residual) = plt.subplots(*((2, 1) if is_journal else (1, 2)))
        period.plot(grid, coefficient * np.sqrt(grid), color=lab.INK, zorder=1)
        lab.points(period, LENGTHS_M, PERIODS_S, yerr=PERIOD_ERROR_MS / MILLISECONDS_PER_SECOND)
        band_colour = lab.tint(lab.PRUSSIAN, FIT_BAND_TINT)
        residual.fill_between(grid, -band_ms, band_ms, color=band_colour, linewidth=0, zorder=0)
        residual.axhline(0, color=lab.INK, linewidth=mpl.rcParams["axes.linewidth"], zorder=1)
        lab.points(residual, LENGTHS_M, residuals_ms, yerr=PERIOD_ERROR_MS)
        for axes in (period, residual):
            axes.set_xlabel(r"$L$ (m)")
            axes.set_xlim(0.15, 1.05)
        ylabels = {period: r"$T$ (s)", residual: r"$T - T_\mathrm{fit}$ (ms)"}
        lab.finish(figure, ylabels, level=not is_journal)
        output = ASSETS / "figures" / f"{medium}.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output)
        plt.close(figure)
    return output


if __name__ == "__main__":
    # finish() measures the labels on the canvas, so it must be the one that typesets them.
    mpl.use("pgf")
    for medium, overlays in MEDIA.items():
        print(draw(medium, overlays))
