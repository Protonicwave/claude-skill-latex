# Figures

A figure is drawn for the page it appears on. Its type matches the text around it in face and size, its width is the width the document gives it, and its caption tells the reader what to see. Scaling a figure drawn at another size changes its type size and line weights with it, which is why a figure pasted from a notebook looks wrong on the page.

## The matplotlib workflow

`new_project.py` copies `laboratory.mplstyle` into the project's `figures/` folder, with the overlay for the profile's medium:

| Medium | Styles | Default size | Type |
|---|---|---|---|
| Document page (report, lab report, notes) | `laboratory` | 175 × 70 mm, the full measure | 9 pt |
| Journal column (paper) | `laboratory`, `journal` | 86 × 92 mm, panels stacked | 8 pt, Computer Modern under pdfLaTeX |
| Slide (16:9 Beamer) | `laboratory`, `slides` | 140 × 50 mm | 10 pt |
| Poster column (A0) | `laboratory`, `poster` | 242 × 110 mm | 28 pt |

The plotting script loads the styles, draws at the width the document will include, and saves through the pgf backend, which typesets every label with LuaLaTeX in the document's own faces:

```python
import matplotlib.pyplot as plt

plt.style.use(["figures/laboratory.mplstyle", "figures/slides.mplstyle"])
figure, axes = plt.subplots()
...
figure.savefig("figures/period.pdf", backend="pgf")
```

A style file cannot choose the backend, so `backend="pgf"` belongs in every `savefig`. Without it matplotlib falls back to its own renderer and DejaVu Sans.

Set the size in the script when the figure is not the full width: `plt.subplots(figsize=(width_in, height_in))`, with the width the fraction of the measure the document uses. Then include it at exactly that fraction: a figure drawn 85 mm wide goes in at `width=0.486\linewidth` on the 175 mm house measure, or better, draw it at the full width and lay two panels side by side in one figure.

The pgf backend runs LuaLaTeX in a temporary folder, so the style's preamble repeats the font settings rather than loading the house package. In a document that does not use the house style, replace `pgf.preamble` with the document's own font lines, or for a pdfLaTeX document use the `journal` overlay's approach: `pgf.texsystem: pdflatex` and an empty preamble for Computer Modern.

## Including a figure

```latex
\begin{figure}[tbp]
  \centering
  \includegraphics[width=\linewidth]{figures/period}
  \caption{Period against length (a), with the fitted small-angle model, and residuals (b). Error bars are one standard error.}
  \label{fig:period}
\end{figure}
```

- Width as a fraction of `\linewidth`, never in centimetres or by `scale` (lint `fixed-figure-width`).
- No file extension, so LaTeX picks the PDF.
- The float goes after the paragraph that first refers to it (lint `float-before-reference`), and the text refers to it with `\cref` (lint `unreferenced-float`).
- On slides, no figure environment: the graphic sits under the frame title with its caption as a line of text below, and the frame title states what it shows. On a poster, Beamer's `figure` environment, which does not float, gives a numbered caption the text refers to with `Figure~\ref{...}`.

## Drawing for the reader

- **Vector, not bitmap.** Plots and diagrams are PDF. PNG and JPEG are for photographs and micrographs, at 300 dpi at the printed size (lint `raster-figure`).
- **Panel labels** (a), (b) sit above the axes, left-aligned, as the axes title the house style places there. Inside the axes they collide with data.
- **No title in the axes.** The caption carries it.
- **Axis labels** name the quantity in italic with its unit in brackets: `$T$ (s)`, `$T - T_\mathrm{fit}$ (ms)`.
- **Colour.** The house cycle is Prussian blue for measurements, near black for models and grey for guides. A continuous quantity uses a perceptually uniform map (viridis, cividis), never jet or another rainbow map, which invents boundaries in smooth data and fails for readers with colour-vision deficiency. Never let colour alone separate two series: change the marker or line style too.
- **Error bars** without caps, as the house style sets; say in the caption what they show (one standard error, 95% interval).
- **Residuals** below the fit, sharing its horizontal axis, when the figure supports a fit.

## Captions

A caption says what the figure shows and what the reader should see in it, and gives the conditions needed to read it: sample, temperature, number of runs, what the error bars mean. It does not repeat the text's argument. A figure from another source says so: "Adapted from~\cite{key}." The house style sets captions in small sans with the label in Prussian.

## Diagrams

Apparatus and schematic diagrams are drawn in TikZ, in the document's faces, or in a vector editor and exported as PDF with fonts embedded. A TikZ diagram reused across documents lives in its own `.tex` file under `figures/` and is brought in with `\input`.
