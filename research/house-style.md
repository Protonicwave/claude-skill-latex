# How the house style was chosen

The house style was picked from rendered pages, not from a description. One report, on Metropolis sampling of the two-dimensional Ising model, was set in three directions, and the user chose between the printed results. The sources are in `specimens/`: `content.tex` holds the shared text and each `specimen-*.sty` holds one direction. Running `latexmk` in that folder rebuilds the three PDFs into `build/`, which is not committed.

## The three directions

| Direction | Text and maths | Furniture | Accent | Measure |
|---|---|---|---|---|
| Journal | STIX Two Text and Math | the same serif, hanging section numbers | none | 122 mm |
| Rubric | TeX Gyre Pagella with Euler maths, old-style figures | the same serif | red for numbers and labels, as early printers used it | 130 mm |
| Laboratory | Erewhon and Erewhon Math | Source Sans 3 for headings, captions, table heads and running head | Prussian blue | 140 mm at first |

Each specimen contains the same title, headings, a derivation, a siunitx table, a matplotlib figure drawn through the pgf backend in that direction's faces, and verified citations. The data come from a seeded simulation (`simulate.py`), so every direction shows the same numbers.

## The choice and what followed it

The user chose Laboratory, and asked for more words on each line. The measure went from 140 mm (about 88 characters) through 150 and 160 mm to 175 mm, about 110 characters at 11 pt, each step rendered and inspected. That is wider than the 45 to 90 characters Butterick allows for body text (`sources.md`); the skill keeps it as the user's decision rather than correcting it.

Inspecting the pages, rather than reading the logs, found most of what the house style now fixes:

- Erewhon Math's solidus has wide side-bearings, so $J/k$ read as "J / k". The style pulls every maths slash in by 2 mu, in the document and in the figure preamble.
- LaTeX's default float fractions sent a figure and a table to a page of floats alone. The style relaxes them so two floats can share a page with text.
- At 175 mm a table floated above the paragraph that defines it, into the previous section. `flafter` now keeps every float below the point where it is written, and the lint reports a float written before its first mention.
- siunitx resets the text family inside tables, undoing per-table font features, unless `reset-text-family = false`.
- Panel labels inside the axes collided with data; they now sit above the axes.
- A 1.3 pt overfull line came from "Boltzmann", which the British patterns do not break; the style gives it a hyphenation exception and sets `\emergencystretch`.

Of these, the log reported two. The rest were visible only on the rendered page, which is why the skill's loop ends with looking at it.

## From specimen to package

`skills/latex/assets/laboratory-base.sty` carries what documents, slides and posters share (faces, maths slash, colours, siunitx settings, natbib, `\dd`, `\head`, `\source` and the record strip); `laboratory.sty` adds the page, headings, captions, floats, listings and theorem styles for the `article` and `report` classes; the two Beamer themes add the slide and poster layouts. The skeletons' pendulum figures are drawn by `skeletons/pendulum.py` with the house mplstyle and an overlay for each medium.
