# Tells of generated LaTeX

The patterns that make a document read as produced by a template or a model, grouped by layer, each with what to do instead. `lint.py` catches those that show in the source and names its rule; the rest need the rendered page. A pattern kept for a stated reason is a decision, not a tell.

## Why they appear

LaTeX's defaults date from the 1980s and suit a printed article read at arm's length: Computer Modern, a column of about 65 characters inside wide margins, floats sent wherever they fit. Most LaTeX on the web accepts them, so a model reproduces them, along with the workarounds people reach for when a default bites: `[H]` from the `float` package, `\vspace{-5mm}`, `\newpage`, `\sloppy`. Each workaround hides a symptom and leaves the cause.

## Page and type

| Tell | Instead |
|---|---|
| Computer Modern because nothing was chosen (`default-typeface`) | A text face with its own maths face (`design.md`), or the house style |
| The class's default text block (`default-margins`) | `geometry`, or the house style; a template's layout stays |
| A sans document with serif maths | A matched sans pair such as Fira Sans with Fira Math |
| Title, author and date centred by `\maketitle` in a report that has a style | The style's title; under a template, the template's |
| Every heading `\section*` | Numbered sections; unnumbered only for front and back matter |
| Bold for emphasis, or bold and italic together | `\emph`, once, at the word that carries the stress |
| Underlining (`underline`) | `\emph`; underlining is a typewriter's substitute |
| `\\` or `\newline` to end paragraphs, `\vspace` and `\noindent` by hand (`manual-layout`, `paragraph-ended-by-line-break`) | A blank line; spacing set once in the style |
| `\sloppy` (`sloppy`) | Fix the lines that overflow; see `typography.md` |
| Stock colour names in the text, red links, boxed links (`named-colour`) | The style's one accent; `hidelinks` or links in the accent |

## Floats

| Tell | Instead |
|---|---|
| `[h]`, `[H]` or `[!h]` on every float (`forced-float-placement`) | `[tbp]`, with the float written after the paragraph that first refers to it |
| A float written before its first reference (`float-before-reference`) | Move it below that paragraph; `flafter` then keeps it there |
| A figure or table the text never mentions (`unreferenced-float`) | Refer to it where the text discusses it, or remove it |
| `center` inside a float (`centre-environment-in-float`) | `\centering` |
| A float without a caption, or with the label before the caption | `\caption`, then `\label` |
| A caption that names the plot ("Graph of T against L") | A caption that says what to see and gives the conditions |
| A page of floats alone, or a gap at a page foot | Check the style's float fractions; move the float or split it |

## Maths and numbers

| Tell | Instead |
|---|---|
| Units typed by hand, `5 cm`, `$5 cm$` (`unit-by-hand`, `italic-unit`) | `\qty{5}{\centi\metre}` |
| Ranges with a hyphen, `3-5` (`hyphen-range`) | `3--5`, or `\numrange{3}{5}` |
| `sin`, `log`, `max` typed as letters (`italic-operator`, `italic-subscript-label`) | `\sin`, `\log`, `T_\mathrm{max}` |
| An italic differential or exponential (`italic-differential`, `italic-constant-e`) | `\dd` and `\mathrm{e}` |
| `$$ ... $$`, `eqnarray`, `\over` (`obsolete-command`) | `equation`, `align`, `\frac` |
| `x` for multiplication (`letter-times`) | `\times` |
| A stacked fraction in running text (`inline-fraction`) | A slash inline, or a display |
| Every equation numbered and none referred to | Number what the text refers to |

## Tables

| Tell | Instead |
|---|---|
| A grid of `\hline` and vertical rules (`ruled-table`) | `booktabs`: three rules, no verticals |
| Caption below the table (`table-caption-below`) | Caption above; a table is read from the top |
| Numbers centred in their column | Aligned on the decimal marker with an `S` column |
| `\resizebox` around a tabular | A table that fits the measure: fewer columns, abbreviated heads, or landscape |
| Units repeated in every cell | Once, in the column head |

## Figures

| Tell | Instead |
|---|---|
| A bitmap plot (`raster-figure`) | A PDF drawn by the plotting code; bitmaps only for photographs |
| A figure sized in centimetres or by `scale` (`fixed-figure-width`) | A fraction of `\linewidth`, with the figure drawn at that width |
| DejaVu Sans labels against a serif text, type far larger or smaller than the caption | The house mplstyle, or the document's faces in the pgf preamble |
| Matplotlib's default blue and orange, the jet colour map | The house cycle; viridis or cividis for a continuous map |
| A title inside the axes repeating the caption | No title; the caption carries it |
| Colour as the only way to tell series apart | Marker shape or line style as well |

## References and citations

| Tell | Instead |
|---|---|
| `Figure \ref{...}` typed by hand, or a space where a tie belongs (`breakable-reference`) | `\cref{...}`, or `Figure~\ref{...}` |
| `\cite{a}\cite{b}` (`split-citation`) | `\cite{a,b}` |
| A hand-made `thebibliography` | BibTeX from `/research`, unless a template demands otherwise |
| Placeholders, `TODO`, `??` left in the text (`leftover-placeholder`) | The content, or a visible marker the report lists |

## Packages

| Tell | Instead |
|---|---|
| `times`, `a4wide`, `epsfig`, `doublespace` and other obsolete packages (`obsolete-package`) | The replacement lint names |
| `fontenc` or `inputenc` under LuaLaTeX (`legacy-encoding`) | Nothing; `fontspec` handles encoding |
| `hyperref` loaded early, `cleveref` before it | Both last, `cleveref` after `hyperref` |
| The same package loaded twice, or a long preamble of packages nothing uses | One line per package the document needs |
