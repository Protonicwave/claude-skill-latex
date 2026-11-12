"""Draw the pendulum figure the profile skeletons include, once for each medium.

Each figure uses the house mplstyle with its medium's overlay, which sets the
size the skeleton includes it at, so its type matches the page around it. The
data are the skeletons' example measurements: the tables there quote the same
numbers.

Usage:
    python research/skeletons/pendulum.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ASSETS = Path(__file__).resolve().parents[2] / "skills" / "latex" / "assets"
LENGTHS_M = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
PERIODS_S = (0.8983, 1.0980, 1.2692, 1.4170, 1.5548, 1.6787, 1.7937, 1.9042, 2.0057)
PERIOD_ERROR_MS = 1.0
MILLISECONDS_PER_SECOND = 1000
# The overlays each medium adds to laboratory.mplstyle; a one-column page stacks the panels.
MEDIA = {"document": (), "journal": ("journal",), "slides": ("slides",), "poster": ("poster",)}
STACKED_MEDIA = frozenset({"journal"})


def fitted_coefficient() -> float:
    """Least-squares a in T = a sqrt(L), every period weighted equally."""
    weighted = sum(
        period * math.sqrt(length) for period, length in zip(PERIODS_S, LENGTHS_M, strict=True)
    )
    return weighted / sum(LENGTHS_M)


def draw(medium: str, overlays: tuple[str, ...]) -> Path:
    styles = [ASSETS / "mplstyle" / f"{name}.mplstyle" for name in ("laboratory", *overlays)]
    coefficient = fitted_coefficient()
    lengths = np.array(LENGTHS_M)
    residuals_ms = (np.array(PERIODS_S) - coefficient * np.sqrt(lengths)) * MILLISECONDS_PER_SECOND
    grid = np.linspace(0.15, 1.05, 200)
    with plt.style.context(styles):
        rows, columns = (2, 1) if medium in STACKED_MEDIA else (1, 2)
        figure, (period, residual) = plt.subplots(rows, columns)
        period.plot(grid, coefficient * np.sqrt(grid), color="C2", zorder=1)
        period.errorbar(
            LENGTHS_M,
            PERIODS_S,
            yerr=PERIOD_ERROR_MS / MILLISECONDS_PER_SECOND,
            fmt="o",
            color="C0",
        )
        period.set_ylabel(r"$T$ (s)")
        residual.axhline(0, color="C3", lw=0.7, ls=(0, (3, 3)), zorder=0)
        residual.errorbar(LENGTHS_M, residuals_ms, yerr=PERIOD_ERROR_MS, fmt="o", color="C0")
        residual.set_ylabel(r"$T - T_\mathrm{fit}$ (ms)")
        for axes, label in ((period, "(a)"), (residual, "(b)")):
            axes.set_xlabel(r"$L$ (m)")
            axes.set_xlim(0.15, 1.05)
            axes.set_title(label)
        output = ASSETS / "figures" / f"{medium}.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, backend="pgf")
        plt.close(figure)
    return output


if __name__ == "__main__":
    for medium, overlays in MEDIA.items():
        print(draw(medium, overlays))
