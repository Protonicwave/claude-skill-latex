import math
import re
from itertools import pairwise

import laboratory as lab
import matplotlib as mpl
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.colors import to_hex, to_rgb, to_rgba_array
from matplotlib.figure import Figure
from matplotlib.text import Text
from new_project import ASSETS

# CIE 1976 lightness of an sRGB colour, for checking that a map's steps look even.
SRGB_LINEAR_LIMIT = 0.04045
LAB_EPSILON = (6 / 29) ** 3


def lightness(rgb: tuple[float, float, float]) -> float:
    linear = [c / 12.92 if c <= SRGB_LINEAR_LIMIT else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    if luminance > LAB_EPSILON:
        return 116 * math.cbrt(luminance) - 16
    return 116 * (luminance / (3 * (6 / 29) ** 2) + 4 / 29) - 16


def map_lightness(name: str, samples: int) -> list[float]:
    colours = mpl.colormaps[name](np.linspace(0, 1, samples))
    return [lightness((red, green, blue)) for red, green, blue, _ in colours]


def two_panels() -> tuple[Figure, Axes, Axes]:
    figure = Figure(figsize=lab.FULL, layout="constrained")
    left, right = figure.subplots(1, 2)
    for axes in (left, right):
        axes.plot([0.2, 1.0], [0.9, 2.0])
        axes.set_xlabel("$L$ (m)")
    return figure, left, right


def text_on(axes: Axes, content: str) -> Text:
    (text,) = [text for text in axes.texts if text.get_text() == content]
    return text


def visible_ticks(axes: Axes) -> list[float]:
    low, high = axes.get_ylim()
    return [tick for tick in axes.get_yticks() if low <= tick <= high]


@pytest.mark.parametrize(
    ("low", "high"),
    [(0.85, 2.05), (0.15, 1.05), (-4, 4), (0, 1e-3), (17, 3500), (45.93, 45.948)],
)
def test_finish_keeps_three_to_seven_ticks_in_steps_of_1_2_or_5(low: float, high: float) -> None:
    figure = Figure()
    axes = figure.subplots()
    axes.set_ylim(low, high)

    lab.finish(figure, {axes: "$y$"})

    ticks = visible_ticks(axes)
    assert 3 <= len(ticks) <= 7
    step = ticks[1] - ticks[0]
    mantissa = step / 10 ** math.floor(math.log10(step))
    assert any(math.isclose(mantissa, allowed) for allowed in (1, 2, 5))


def test_finish_keeps_the_period_axis_at_whole_and_half_seconds() -> None:
    figure = Figure()
    axes = figure.subplots()
    axes.set_ylim(0.85, 2.05)

    lab.finish(figure, {axes: "$T$ (s)"})

    assert visible_ticks(axes) == pytest.approx([1.0, 1.5, 2.0])


def test_finish_leaves_a_log_axis_alone() -> None:
    figure = Figure()
    axes = figure.subplots()
    axes.set_yscale("log")
    axes.set_ylim(1e-15, 1e5)
    locator = axes.yaxis.get_major_locator()

    lab.finish(figure, {axes: "$P$"})

    assert axes.yaxis.get_major_locator() is locator


def test_finish_sets_the_axes_clear_of_the_data() -> None:
    figure = Figure()
    axes = figure.subplots()

    lab.finish(figure, {axes: "$y$"})

    offset_pt = mpl.rcParams["font.size"] * lab.SPINE_OFFSET_EM
    assert axes.spines["left"].get_position() == ("outward", offset_pt)
    assert axes.spines["bottom"].get_position() == ("outward", offset_pt)


def test_finish_sets_the_panel_letter_left_of_a_level_y_label() -> None:
    figure, left, right = two_panels()

    ylabels = {left: "$T$ (s)", right: r"$T - T_\mathrm{fit}$ (ms)"}

    lab.finish(figure, ylabels)
    figure.draw_without_rendering()

    for axes, letter in ((left, "a"), (right, "b")):
        ylabel = ylabels[axes]
        letter_box = text_on(axes, letter).get_window_extent()
        label_box = text_on(axes, ylabel).get_window_extent()
        tick_box = axes.yaxis.get_tightbbox()
        assert tick_box is not None
        assert letter_box.x1 < label_box.x0
        assert letter_box.x0 == pytest.approx(tick_box.x0, abs=0.5)
        assert min(letter_box.y0, label_box.y0) > axes.get_window_extent().y1
        assert axes.get_ylabel() == ""


def test_finish_sets_the_panel_letter_on_the_level_y_label_baseline() -> None:
    figure, left, right = two_panels()

    lab.finish(figure, {left: "$T$ (s)", right: "$r$ (ms)"})

    letter, ylabel = text_on(left, "a"), text_on(left, "$T$ (s)")
    assert letter.get_verticalalignment() == ylabel.get_verticalalignment() == "baseline"
    letter_anchor = letter.get_transform().transform(letter.get_position())
    ylabel_anchor = ylabel.get_transform().transform(ylabel.get_position())
    assert letter_anchor[1] == pytest.approx(ylabel_anchor[1])


def test_finish_sets_the_panel_letter_above_a_rotated_y_label() -> None:
    figure, left, right = two_panels()

    lab.finish(figure, {left: "$T$ (s)", right: "$r$ (ms)"}, level=False)
    figure.draw_without_rendering()

    for axes, letter in ((left, "a"), (right, "b")):
        letter_box = text_on(axes, letter).get_window_extent()
        label_box = axes.yaxis.label.get_window_extent()
        assert not letter_box.overlaps(label_box)
        assert letter_box.x0 == pytest.approx(label_box.x0, abs=0.5)
        assert letter_box.y0 > axes.get_window_extent().y1


def test_finish_sets_the_panel_letter_in_bold_sans() -> None:
    figure, left, right = two_panels()

    lab.finish(figure, {left: "$T$ (s)", right: "$r$ (ms)"})

    letter = text_on(left, "a")
    assert letter.get_fontfamily() == ["sans-serif"]
    assert letter.get_fontweight() == "bold"


def test_finish_letters_no_single_axes() -> None:
    figure = Figure()
    axes = figure.subplots()

    lab.finish(figure, {axes: "$T$ (s)"})

    assert [text.get_text() for text in axes.texts] == ["$T$ (s)"]


def test_finish_rejects_a_y_label_already_set() -> None:
    figure = Figure()
    axes = figure.subplots()
    axes.set_ylabel("$T$ (s)")

    with pytest.raises(ValueError, match="already set"):
        lab.finish(figure, {axes: "$T$ (s)"})


def test_finish_rejects_no_axes() -> None:
    with pytest.raises(ValueError, match="at least one axes"):
        lab.finish(Figure(), {})


def test_points_draw_a_white_edged_marker_over_a_lighter_error_bar() -> None:
    axes = Figure().subplots()

    container = lab.points(axes, [1, 2], [3, 4], yerr=0.1)

    marker, _, (error_bars,) = container.lines
    assert marker.get_markeredgecolor() == "white"
    marker_rgb = to_rgb(lab.PRUSSIAN)
    error_rgb = to_rgba_array(error_bars.get_colors())[0, :3]
    assert all(error > own for error, own in zip(error_rgb, marker_rgb, strict=True))


def test_sizes_are_the_measure_and_its_fractions() -> None:
    assert lab.FULL[0] * lab.MILLIMETRES_PER_INCH == pytest.approx(150)
    assert lab.TWO_THIRDS[0] == pytest.approx(lab.FULL[0] * 2 / 3)
    assert lab.HALF[0] == pytest.approx(lab.FULL[0] / 2)


def test_register_colormaps_adds_both_maps_once_even_when_called_twice() -> None:
    lab.register_colormaps()
    first = mpl.colormaps["laboratory"]

    lab.register_colormaps()

    assert mpl.colormaps["laboratory"] == first
    assert "laboratory_diverging" in mpl.colormaps


def test_the_sequential_map_darkens_steadily() -> None:
    lab.register_colormaps()

    levels = map_lightness("laboratory", 64)

    assert all(darker < lighter for lighter, darker in pairwise(levels))


def test_the_diverging_map_is_equally_strong_either_side_of_zero() -> None:
    lab.register_colormaps()

    levels = map_lightness("laboratory_diverging", 65)

    for below, above in zip(levels[:32], reversed(levels[33:]), strict=True):
        assert below == pytest.approx(above, abs=1.5)


def test_series_colours_agree_in_latex_the_style_and_the_helper() -> None:
    package = (ASSETS / "laboratory-base.sty").read_text(encoding="utf-8")
    defined = dict(re.findall(r"\\definecolor\{(\w+)\}\{HTML\}\{(\w{6})\}", package))
    assert r"\colorlet{seriesA}{prussian}" in package
    latex = [defined[name] for name in ("prussian", "seriesB", "seriesC", "seriesD")]
    style = mpl.rc_params_from_file(
        ASSETS / "mplstyle" / "laboratory.mplstyle", use_default_template=False
    )
    cycle = [to_hex(entry["color"]) for entry in style["axes.prop_cycle"]]

    assert [f"#{code.lower()}" for code in latex] == cycle
    assert [colour.lower() for colour in (lab.PRUSSIAN, lab.TERRACOTTA, lab.INK, lab.GREY)] == cycle
