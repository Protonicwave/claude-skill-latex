"""Laboratory house helpers for matplotlib: figure sizes, colours, points and finishing.

laboratory.mplstyle sets what matplotlib's settings can hold. This module sets
what they cannot: tick density, detached axes, panel letters, level y labels,
measured points with a white edge and the house colour maps.

Keep it in figures/ beside the scripts that import it, and draw on the pgf
canvas, so finish() measures every label as LuaLaTeX sets it:

    import matplotlib
    import matplotlib.pyplot as plt

    import laboratory as lab

    matplotlib.use("pgf")
    plt.style.use("figures/laboratory.mplstyle")
    figure, (fit, residual) = plt.subplots(1, 2, figsize=lab.FULL)
    ...
    lab.finish(figure, {fit: r"$T$ (s)", residual: r"$T - T_\\mathrm{fit}$ (ms)"})
    figure.savefig("figures/period.pdf")
"""

from __future__ import annotations

import string
from collections.abc import Mapping

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.container import ErrorbarContainer
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import ScaledTranslation
from numpy.typing import ArrayLike

MILLIMETRES_PER_INCH = 25.4
POINTS_PER_INCH = 72


def _inches(width_mm: float, height_mm: float) -> tuple[float, float]:
    return width_mm / MILLIMETRES_PER_INCH, height_mm / MILLIMETRES_PER_INCH


# figsize for a figure included at width=\linewidth, 0.667\linewidth and
# 0.5\linewidth on the 150 mm document measure, so its type stays at 9 pt.
FULL = _inches(150, 60)
TWO_THIRDS = _inches(100, 70)
HALF = _inches(75, 60)

# seriesA to seriesD of laboratory-base.sty, in the order of the style's colour
# cycle: measurements, a second measured series, models, guides.
PRUSSIAN = "#1F4A73"
TERRACOTTA = "#B5562C"
INK = "#1A1A1A"
GREY = "#737373"
PAPER = "#F6F3EC"

# Paper to deep Prussian for a field. Prussian through paper to deep terracotta
# for a signed quantity, each arm's stops matched in lightness so equal values
# either side of zero look equally strong.
SEQUENTIAL_STOPS = (PAPER, "#B8CCDD", "#6F96BC", "#2F6293", PRUSSIAN, "#0E2238")
DIVERGING_STOPS = (PRUSSIAN, "#4775A4", "#95B1CF", PAPER, "#D9A381", TERRACOTTA, "#773416")

# Proportions of the style's own sizes, so the slide and poster overlays scale them too.
MARKER_SCALE = 1.3  # the white edge eats into the marker, so it is drawn larger
MARKER_EDGE_FRACTION = 0.12
ERROR_BAR_WIDTH_FRACTION = 0.7
ERROR_BAR_TINT = 0.45
SPINE_OFFSET_EM = 1 / 3
LABEL_RISE_EM = 5 / 9

# Steps of 1, 2 or 5 cannot always give four to six ticks, because the count
# jumps by 2 to 2.5 times between steps; these settings give three to five on
# most ranges and up to seven on a few.
TICK_STEPS = (1, 2, 5, 10)
TICK_INTERVALS = 5
MIN_TICKS = 3


def register_colormaps() -> None:
    """Add the house maps to matplotlib as "laboratory" and "laboratory_diverging".

    Calling it again does nothing, so every script can call it.
    """
    for name, stops in (
        ("laboratory", SEQUENTIAL_STOPS),
        ("laboratory_diverging", DIVERGING_STOPS),
    ):
        if name not in mpl.colormaps:
            mpl.colormaps.register(LinearSegmentedColormap.from_list(name, stops))


def tint(colour: str, amount: float) -> tuple[float, float, float]:
    """Mix a colour towards white: amount 0 keeps it, 1 gives white."""
    red, green, blue = to_rgb(colour)
    return (red + (1 - red) * amount, green + (1 - green) * amount, blue + (1 - blue) * amount)


def points(
    axes: Axes, x: ArrayLike, y: ArrayLike, yerr: ArrayLike | None = None, colour: str = PRUSSIAN
) -> ErrorbarContainer:
    """Measured values: a white-edged marker over a thinner, lighter error bar."""
    marker_size = mpl.rcParams["lines.markersize"] * MARKER_SCALE
    return axes.errorbar(
        x,
        y,
        yerr=yerr,
        fmt="o",
        color=colour,
        ecolor=tint(colour, ERROR_BAR_TINT),
        elinewidth=mpl.rcParams["lines.linewidth"] * ERROR_BAR_WIDTH_FRACTION,
        markersize=marker_size,
        markeredgecolor="white",
        markeredgewidth=marker_size * MARKER_EDGE_FRACTION,
        zorder=3,
    )


def finish(figure: Figure, ylabels: Mapping[Axes, str], *, level: bool = True) -> None:
    """Tidy each axes' ticks and spines, give it its y label and, if there are several, a letter.

    Call it once, after everything else is drawn: it measures the tick labels to
    place the letters and labels. Letters run a, b, c in the order of ylabels,
    in bold sans; a single axes gets none. A level y label sits above the axis;
    level=False runs it up the axis instead, as journals expect.

    Raises ValueError for no axes, more axes than letters, or an axes whose y
    label was already set.
    """
    if not ylabels:
        raise ValueError("expected at least one axes to finish, got none")
    if len(ylabels) > len(string.ascii_lowercase):
        raise ValueError(f"expected at most 26 axes to letter, got {len(ylabels)}")
    for axes in ylabels:
        if axes.get_ylabel():
            raise ValueError(f"y label {axes.get_ylabel()!r} already set; give it to finish()")
    font_size_pt = mpl.rcParams["font.size"]
    for axes, ylabel in ylabels.items():
        _tidy(axes, font_size_pt * SPINE_OFFSET_EM)
        if not level:
            axes.set_ylabel(ylabel)
    figure.draw_without_rendering()
    rise_in = font_size_pt * LABEL_RISE_EM / POINTS_PER_INCH
    for letter, (axes, ylabel) in zip(string.ascii_lowercase, ylabels.items(), strict=False):
        axes_left_px = axes.get_window_extent().x0
        spine_left_px = axes.spines["left"].get_window_extent().x0
        # The y axis' extent spans its tick labels, and its label when it runs up the axis.
        axis_extent = axes.yaxis.get_tightbbox()
        letter_left_px = spine_left_px if axis_extent is None else axis_extent.x0
        if level:
            ylabel_left_in = (spine_left_px - axes_left_px) / figure.dpi
            _above(figure, axes, ylabel, ylabel_left_in, rise_in)
        if len(ylabels) > 1:
            letter_left_in = (letter_left_px - axes_left_px) / figure.dpi
            letter_text = _above(figure, axes, letter, letter_left_in, rise_in)
            letter_text.set(family="sans-serif", weight="bold")


def _tidy(axes: Axes, spine_offset_pt: float) -> None:
    for axis in (axes.xaxis, axes.yaxis):
        if axis.get_scale() == "linear":
            axis.set_major_locator(
                MaxNLocator(nbins=TICK_INTERVALS, steps=list(TICK_STEPS), min_n_ticks=MIN_TICKS)
            )
    for side in ("left", "bottom"):
        axes.spines[side].set_position(("outward", spine_offset_pt))


def _above(figure: Figure, axes: Axes, text: str, left_in: float, rise_in: float) -> Text:
    """Text at left_in from the axes' left edge, its baseline rise_in above the axes."""
    offset = ScaledTranslation(left_in, rise_in, figure.dpi_scale_trans)
    return axes.text(
        0, 1, text, transform=axes.transAxes + offset, ha="left", va="baseline", clip_on=False
    )
