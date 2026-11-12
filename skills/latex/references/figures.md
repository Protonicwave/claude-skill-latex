# Figures

A figure is drawn for the page it appears on. Its type matches the text around it in face and size, its width is the width the document gives it, and its caption tells the reader what to see. Scaling a figure drawn at another size changes its type size and line weights with it, which is why a figure pasted from a notebook looks wrong on the page.

## The matplotlib workflow

`new_project.py` copies three things into the project's `figures/` folder: `laboratory.mplstyle`, the overlay for the profile's medium, and `laboratory.py`, the figure helper. The style sets what matplotlib's settings can hold; the helper sets what they cannot, such as tick density, panel letters and level axis labels.

| Medium | Styles | Default size | Type |
|---|---|---|---|
| Document page (report, lab report, notes) | `laboratory` | 150 × 60 mm, the full measure | 9 pt |
| Journal column (paper) | `laboratory`, `journal` | 86 × 92 mm, panels stacked | 8 pt, Computer Modern under pdfLaTeX |
| Slide (16:9 Beamer) | `laboratory`, `slides` | 140 × 50 mm | 10 pt |
| Poster column (A0) | `laboratory`, `poster` | 242 × 110 mm | 28 pt |

A plotting script lives in `figures/` beside the helper and runs from the project folder, as `python figures/period.py`, so Python finds `laboratory.py` next to it:

```python
import matplotlib
import matplotlib.pyplot as plt

import laboratory as lab

matplotlib.use("pgf")
plt.style.use("figures/laboratory.mplstyle")

figure, (fit, residual) = plt.subplots(1, 2, figsize=lab.FULL)
fit.plot(grid, model, color=lab.INK)
lab.points(fit, length, period, yerr=period_error)
...
for axes in (fit, residual):
    axes.set_xlabel(r"$L$ (m)")
lab.finish(figure, {fit: r"$T$ (s)", residual: r"$T - T_\mathrm{fit}$ (ms)"})
figure.savefig("figures/period.pdf")
```

`matplotlib.use("pgf")` comes before any drawing, because a style file cannot choose the backend. The pgf backend typesets every label with LuaLaTeX in the document's own faces, and `finish` measures the labels on that canvas to place the panel letters. Without it matplotlib falls back to DejaVu Sans, and the letters sit where DejaVu's widths put them.

For a slide or poster, load the overlay too, `plt.style.use(["figures/laboratory.mplstyle", "figures/slides.mplstyle"])`, and leave out `figsize`: the overlay sets the size, and the helper scales its markers and spacing from the overlay's type size.

On the 150 mm document measure the helper names three sizes. Draw at one and include the figure at exactly the matching fraction of `\linewidth`:

| Draw at | Include at | Use |
|---|---|---|
| `lab.FULL`, 150 × 60 mm | `width=\linewidth` | two panels side by side, or one wide plot |
| `lab.TWO_THIRDS`, 100 × 70 mm | `width=0.667\linewidth` | one plot that needs some height, such as a spectrum |
| `lab.HALF`, 75 × 60 mm | `width=0.5\linewidth` | one small plot; two of them side by side are better drawn as one full-width figure |

Draw two related panels as one full-width figure rather than two half-width files, so they share a size and line up.

The pgf backend runs LuaLaTeX in a temporary folder, so the style's preamble repeats the font settings rather than loading the house package. In a document that does not use the house style, replace `pgf.preamble` with the document's own font lines, or for a pdfLaTeX document use the `journal` overlay's approach: `pgf.texsystem: pdflatex` and an empty preamble for Computer Modern.

## The helper

- **`lab.finish(figure, ylabels)`** is the last call before `savefig`, once the data and x labels are drawn. `ylabels` maps each axes to its y label. It gives every linear axis three to five ticks in steps of 1, 2 or 5 (up to seven on a few ranges), and leaves a log axis alone. It sets both axes clear of the data by a third of the type size, 3 pt on a document page, so they do not meet in the corner. It sets each y label level, above the axis, so it reads without tilting the head. With more than one axes it letters them a, b, c in bold sans, in the order of `ylabels`, on the label's baseline; a single plot gets no letter. Give the y label to `finish`, not to `set_ylabel`: it refuses an axes whose label is already set. For a journal, pass `level=False` to run the labels up the axis as the journal's own figures do.
- **`lab.points(axes, x, y, yerr=...)`** draws measured values as white-edged markers over thinner, lighter error bars without caps, so the point reads first and overlapping points stay apart. `colour=lab.TERRACOTTA` draws a second series.
- **`lab.register_colormaps()`** adds the house maps to matplotlib, after which `cmap="laboratory"` or `cmap="laboratory_diverging"` uses them. Calling it twice does no harm.
- **`lab.tint(colour, amount)`** mixes a colour towards white, for a band or a fill behind the data.

## Including a figure

```latex
\begin{figure}[tbp]
  \centering
  \includegraphics[width=\linewidth]{figures/period}
  \caption{\lead{The small-angle model fits every length.} Period against length~\marker{seriesA}, with the fitted model~\linekey{seriesC} (a), and residuals from the fit (b). Error bars are one standard error.}
  \label{fig:period}
\end{figure}
```

- Width as a fraction of `\linewidth`, never in centimetres or by `scale` (lint `fixed-figure-width`).
- No file extension, so LaTeX picks the PDF.
- The float goes after the paragraph that first refers to it (lint `float-before-reference`), and the text refers to it with `\cref` (lint `unreferenced-float`).
- On slides, no figure environment: the graphic sits under the frame title with its caption as a line of text below, and the frame title states what it shows. On a poster, Beamer's `figure` environment, which does not float, gives a numbered caption the text refers to with `Figure~\ref{...}`.

## Drawing for the reader

- **Vector, not bitmap.** Plots and diagrams are PDF. PNG and JPEG are for photographs and micrographs, at 300 dpi at the printed size (lint `raster-figure`).
- **One face for the data.** The style sets every label in Erewhon, the text face, because tick labels on a log axis and every symbol in an axis label are maths in Erewhon Math. A sans legend beside serif ticks puts two designs in one figure. The panel letters are the one exception: they are labels, like "Figure 1", and share its sans.
- **Panel letters** sit above the top left corner, set by `finish`. Inside the axes they collide with data. The caption refers to them as (a) and (b).
- **Ticks.** `finish` thins a linear axis; a log axis is left to you. Matplotlib labels a log axis every decade or every few, which crowds an axis spanning twenty decades; set the ticks yourself, keeping only those inside the axis's range, since `set_yticks` widens the axis to show every tick it is given:
  ```python
  low, high = axes.get_ylim()
  decades = 10.0 ** np.arange(-15, 16, 5)
  axes.set_yticks(decades[(decades >= low) & (decades <= high)])
  ```
- **No title in the axes.** The caption carries it.
- **Axis labels** name the quantity in italic with its unit in brackets: `$T$ (s)`, `$T - T_\mathrm{fit}$ (ms)`. Scale the data so the axis needs no multiplier and put the power in the unit, as `(ms)` does; matplotlib's `1e-3` above the axis would collide with the level label.
- **Colour.** The helper names the house colours, which are `seriesA` to `seriesD` in LaTeX and the style's colour cycle in the same order: `lab.PRUSSIAN` for measurements, `lab.TERRACOTTA` for a second measured series, `lab.INK` (near black) for models and `lab.GREY` (45 per cent) for guides. A caption names a mark in its own colour with `\marker{seriesB}` or `\linekey{seriesC}`, so it never has to say "the orange points". A grey set by hand is no lighter than `"0.45"`, and text in a figure no lighter than `"0.3"`; paler greys fade out in print. Never let colour alone separate two series: change the marker or line style too.
- **Colour maps.** A field uses `laboratory`, from paper white to deep Prussian. A signed quantity uses `laboratory_diverging`, from Prussian through paper to deep terracotta, centred on zero with `vmin=-limit, vmax=limit`; its two arms match in lightness, so equal values either side of zero look equally strong. Both darken evenly, as viridis and cividis do. Never jet or another rainbow map, which invents boundaries in smooth data and fails for readers with colour-vision deficiency.
- **Label series at their ends**, in their own colour, rather than in a legend, so the reader does not match symbols to a key:
  ```python
  axes.annotate(r"$12 \times 12$", (x[-1], y[-1]), color=lab.TERRACOTTA,
                xytext=(6, 0), textcoords="offset points", ha="left", va="center")
  ```
  Keep a legend only when the ends crowd together.
- **Error bars** come from `lab.points`; say in the caption what they show (one standard error, 95% interval).
- **The fit's uncertainty** is a band behind the data, filled with `lab.tint(lab.PRUSSIAN, 0.86)` and named in the caption. The skeletons' residual panel shows one.
- **Residuals** beside or below the fit, sharing its horizontal scale, when the figure supports a fit.

## Captions

A caption opens with its point in `\lead{...}`, then says what the figure shows and gives the conditions needed to read it: sample, temperature, number of runs, what the error bars and bands mean. It does not repeat the text's argument. A figure from another source says so: "Adapted from~\cite{key}." The house style sets captions in small sans with the label in Prussian.

## Diagrams

Apparatus and schematic diagrams are drawn in TikZ, in the document's faces, or in a vector editor and exported as PDF with fonts embedded. A TikZ diagram reused across documents lives in its own `.tex` file under `figures/` and is brought in with `\input`.
