# Structure

## Project layout

```
main.tex            the document; preamble short, settings in the style
chapters/           one file per chapter, for a report
figures/            PDFs, the scripts or mplstyle files that draw them, TikZ sources
refs.bib            from /research
laboratory*.sty     the house packages, copied by new_project.py
latexmkrc           engine, build folder, BibTeX search path
build/              everything the build writes; never committed
.vscode/            LaTeX Workshop settings
```

Commit the sources, the figure scripts and the figure PDFs. Ignore `build/`.

A report brings in chapters with `\include{chapters/method}`, which starts a page and lets `\includeonly` build one chapter while drafting. Smaller pieces such as a TikZ diagram use `\input`. Paths are relative to `main.tex`'s folder, as TeX resolves them; lint reports a file it cannot read as a defect.

## Preamble

The preamble of a house document is the class line, `\usepackage{laboratory}`, the title fields and any package the content needs beyond the style. Settings for type, page, captions and floats belong in the style, so they change in one place. A document-specific macro is defined once in the preamble with a comment saying what it is for.

Package order matters in three places:

- `amsmath` before `unicode-math`, and `fontspec` before both font commands. The house style does this.
- `hyperref` after almost everything, and `cleveref` after `hyperref`. The house style loads both last, so a package the document adds goes before `\usepackage{laboratory}` if it must precede them, or after if it does not care.
- `float`, if a template loads it, before `hyperref`.

## Labels and cross-references

Every numbered element a reader may be sent to gets a label with a kind prefix: `fig:`, `tab:`, `eq:`, `sec:`, `ch:`, `def:`, `ex:`, `lst:`. The label goes after `\caption` in a float and inside the environment for an equation or theorem.

Refer with `\cref{fig:period}` mid-sentence and `\Cref{fig:period}` at the start of one. The house style loads cleveref with `capitalise` and `noabbrev`, so both print "Figure 1"; REVTeX papers follow APS and print "Fig. 1" mid-sentence. Never type the number by hand. Several at once: `\cref{fig:period,fig:residuals}`. The Beamer themes do not load cleveref, so a poster writes `Figure~\ref{fig:period}` and `Equation~\eqref{eq:period}`.

`build.py` reports undefined and multiply defined labels as defects.

## Titles, abstracts and the house macros

| Macro | Purpose |
|---|---|
| `\title`, `\author`, `\date` | as usual; the house `\maketitle` sets them with the record strip |
| `\source{...}` | the repository, notebook or data folder behind the document, shown in the record strip in monospace; omit it and the field disappears |
| `\head{...}` | a table column head in the furniture face |
| `\dd` | the upright differential |
| `definition`, `example` | numbered by section, headed in the furniture face; referred to as Definition 1.1 and Example 1.2 |
| `lstlisting` | code in IBM Plex Mono with the house rule; `\cref` prints "Listing 1" |

Maths in a title, section heading or frame title also goes into PDF bookmarks, which hold only text. Give a plain-text twin: `\title{Measuring \texorpdfstring{$g$}{g} with a pendulum}`. Without one, `build.py` passes on hyperref's warning "Token not allowed in a PDF string" with the heading's line.

The abstract in the house style is one paragraph at the full measure, opening with a run-in "Abstract" in Prussian sans.

## Sectioning

- Number every section that holds content; `\section*` only for front and back matter such as acknowledgements or a declaration.
- `\appendix` before appendices, so they number A, B, C.
- A contents page in a report and in notes, not in a lab report.
- `\clearpage` before an appendix or a declaration a template requires on its own page is a stated reason for manual layout; elsewhere let LaTeX break pages.

## Building outside the skill

The house `latexmkrc` sets the engine, the `build/` folder, SyncTeX and file:line errors, so `latexmk` run in the project folder and LaTeX Workshop's latexmk recipe build the same PDF as `build.py`. LaTeX Workshop reads the output folder from `.vscode/settings.json`. On Windows both need a Perl (`SKILL.md`, Requirements).
