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

The user chose Laboratory, and asked for more words on each line. The measure went from 140 mm (about 88 characters) through 150 and 160 mm to 175 mm, about 110 characters at 11 pt, each step rendered and inspected. That is wider than the 45 to 90 characters Butterick allows for body text (`sources.md`); the skill kept it as the user's decision rather than correcting it.

On 11 November 2026 the user reviewed a ten-page report at 175 mm and narrowed the measure to 150 mm, about 95 characters, with 30 mm side margins. The same review set figure text in the text face, bold panel labels, darker greys and fewer log ticks; regular-weight table heads, tables that fill the measure or hold their caption to their own width, and wider table rows; an en space after caption labels, an indented abstract, and a `compact` option that runs a short report's chapters on.

Inspecting the pages, rather than reading the logs, found most of what the house style now fixes:

- Erewhon Math's solidus has wide side-bearings, so $J/k$ read as "J / k". The style pulls every maths slash in by 2 mu, in the document and in the figure preamble.
- LaTeX's default float fractions sent a figure and a table to a page of floats alone. The style relaxes them so two floats can share a page with text.
- At 175 mm a table floated above the paragraph that defines it, into the previous section. `flafter` now keeps every float below the point where it is written, and the lint reports a float written before its first mention.
- siunitx resets the text family inside tables, undoing per-table font features, unless `reset-text-family = false`.
- Panel labels inside the axes collided with data; they now sit above the axes.
- A 1.3 pt overfull line came from "Boltzmann", which the British patterns do not break; the style gives it a hyphenation exception and sets `\emergencystretch`.

Of these, the log reported two. The rest were visible only on the rendered page, which is why the skill's loop ends with looking at it.

## The design round

Later the same day the lab report and report skeletons were set twice, once in the style as it stood and once with a set of coded proposals, and the user chose between the rendered pages by code. Three faults on those pages were fixed whatever the choice: a caption held to a narrow table's width hyphenated "selected"; table heads meant to be sans came out in the serif maths face, because siunitx set them; and the report skeleton left its five-row table alone on a page, because a short chapter with two floats flushed the second onto a page of its own when the chapter ended.

The proposals gave documents the details the slides already had and made the parts of a page agree with each other. Section numbers and bullets hang in the left margin, so headings, lists and text share one edge. A kicker names the document above the title. Chapters open lower on the page under a light Prussian numeral and the record strip's accent rule, and the contents page is set in the furniture face. The page number sits at the foot of every page instead of moving between head and foot. A table hangs from the left edge with its caption, which is ragged and at most two thirds of the measure, rather than being centred under a caption held to its width. Units sit under their symbols in small grey sans, and the table rules repeat the record strip's colours. A plan the user had written for another project supplied the coded tags, risk levels, statement block, run-in heads and Gantt chart; none of its text was used. For figures the round chose tidier ticks, level axis labels and house colour maps.

## From specimen to package

`skills/latex/assets/laboratory-base.sty` carries what documents, slides and posters share (faces, maths slash, colours, siunitx settings, natbib, `\dd`, `\head`, `\source` and the record strip); `laboratory.sty` adds the page, headings, chapter openings, contents, lists, captions, floats, the statement block, listings and theorem styles for the `article` and `report` classes; the two Beamer themes add the slide and poster layouts. The skeletons' pendulum figures are drawn by `skeletons/pendulum.py` with the house mplstyle and an overlay for each medium.
