# Typography

Conventions for running text. The house style sets the face, measure and spacing once; these rules govern what goes into the source.

## Language

Load `babel` with `british`, so words break by British patterns and the captions read "Contents" and "References". The house style does this. A proper name the patterns do not know gets a hyphenation exception in the style, as the house style does for `Boltz-mann`, rather than `\-` in every occurrence.

## Measure and leading

The house measure is 150 mm, about 95 characters at 11 pt, by the user's choice (`design.md`). At that width the class's leading is enough for the eye to find the next line. Under a template, the template's measure stands.

Leave the class's leading alone. LaTeX's 11 pt text already sits on a 13.6 pt baseline, about 1.24 times the type size, which is what a handbook means by single spacing. `\linespread` and `setspace` multiply that baseline, so a handbook's "1.0 to 1.15" is met by the default and exceeded by `\linespread{1.15}`. Never `\renewcommand{\baselinestretch}` inside the document body.

## Type sizes

The standard classes set these sizes, in points, for their 11 and 12 pt options. Use the table to check a handbook's minimum sizes; the house style's captions are `\small`.

| Command | 11 pt class | 12 pt class |
|---|---|---|
| `\scriptsize` | 8 | 8 |
| `\footnotesize` | 9 | 10 |
| `\small` | 10 | 10.95 |
| `\normalsize` | 10.95 | 12 |
| `\large` | 12 | 14.4 |
| `\Large` | 14.4 | 17.28 |

Footnotes are `\footnotesize`, and the standard classes set the bibliography at the body size. Figure labels take their size from the plotting style, not the class: the house figures use 9 pt on the page and 8 pt in a journal column.

## Dashes and ranges

| Mark | Source | Use |
|---|---|---|
| hyphen | `-` | compound words: *two-level system*, *least-squares fit* |
| en dash | `--` | ranges, `pages 25--30`, `\numrange{3}{5}`; joint names, *Born--Oppenheimer* |
| minus | `$-3$` or `\num{-3}` | negative numbers and subtraction, always in maths or siunitx |
| em dash | `---` | none in the user's prose |

The user's rule bans em dashes and en dashes used as punctuation; it does not touch an en dash that marks a range, which is a typographic sign like the minus. Where a writer or module bans the en dash outright, write ranges in words: `\qtyrange[range-phrase={~to~}]{0.2}{1.0}{\metre}`, and drop `compress` from natbib's options so a run of citations prints every number rather than a range.

## Quotation marks

Open with ` `` ` or `` ` `` and close with `''` or `'`; a straight `"` sets as a closing mark at the start of a word. `\enquote{...}` from `csquotes`, which the house style loads, chooses and nests the marks for the document's language. British usage puts single marks outside and double inside.

## Ties and spacing

- A tie (`~`) keeps a number or citation on the line of the word before it: `Section~3`, `shown~\cite{key}`, `Figure~\ref{fig:a}`. `\cref` inserts its own.
- siunitx puts the right space between a number and its unit; never type it.
- The house style sets `\frenchspacing`, one space after every full stop, so `e.g.` and initials need nothing. Without it, write `e.g.\ ` after an abbreviation that ends mid-sentence.
- `\dots` for an ellipsis, never three full stops.

## Emphasis

`\emph` for stress and for a term at its definition, once. No bold in running text, no bold italic, no underlining, no capitals for emphasis. Bold belongs to headings and to vectors in maths.

## Headings

Sentence case, no full stop, numbered. Three levels at most in a report or notes (`\chapter`, `\section`, `\subsection`), two in a lab report. A heading is never the last line on a page; if one is, look for the float or display that pushed it there before forcing a break.

## Overfull and underfull lines

`build.py` reports any line more than 1 pt into the margin and any underfull line at badness 10000. Cure an overfull line in this order, building after each step:

1. Make sure `microtype` is loaded; the house style loads it. Its protrusion and expansion absorb most small overflows.
2. A long word that will not break: give it a hyphenation exception in the style, or `\-` once if it occurs once.
3. A URL, path or identifier: `\url` or `\path`, which break at slashes and dots, or `\texttt` with `\allowbreak` after separators.
4. A display or table: split the equation with `multline` or `split`, narrow the table (`tables.md`).
5. Raise `\emergencystretch` in the style if it is not set; the house style sets 1.5 em.
6. Reword. That is a `/writing` change, so name the sentence and the cause in the report.

Never `\sloppy`, `\hbadness=10000` or `\hfuzz` to silence the log: they hide the line without fixing it.

An underfull line at badness 10000 almost always comes from `\\` or `\newline` at the end of a paragraph, or from `\linebreak` in justified text. Remove the forced break.

## Lists and code

A list holds discrete parallel items: apparatus, steps, options. An argument is prose. Keep `itemize` to one level in documents and two on slides. The house style hangs a list's labels in the left margin, as it hangs section numbers, so the items start on the text's edge; the bullets are the Prussian squares of the slides.

Inline identifiers go in `\texttt`, short code in `\lstinline`, and longer code in a `lstlisting` environment, which the house style draws with a Prussian rule. A listing the text refers to takes a `caption` and `label` like a float.
