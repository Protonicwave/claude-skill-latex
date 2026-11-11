# Tables

A table is read from the top, column by column. It needs a caption above it, three horizontal rules, columns aligned by their content, and units stated once in the heads. The house style loads `booktabs`, `tabularx` and `siunitx` for this.

## The pattern

A table of a few columns stays at its natural width inside a `threeparttable`, which holds the caption to the table's width:

```latex
\begin{table}[tbp]
  \centering
  \begin{threeparttable}
    \caption{Measured and fitted periods at selected lengths.}
    \label{tab:period}
    \begin{tabular}{
      S[table-format=1.1]
      S[table-format=1.4(2)]
      S[table-format=1.4]
      S[table-format=-1.1]
    }
      \toprule
      \multicolumn{2}{c}{\spanhead{Measured}} & \multicolumn{2}{c}{\spanhead{Fitted}} \\
      \cmidrule(lr){1-2} \cmidrule(lr){3-4}
      {\colhead{$L$}{\metre}} & {\colhead{$T$}{\second}} & {\colhead{$T_\mathrm{fit}$}{\second}} & {\colhead{$T - T_\mathrm{fit}$}{\milli\second}} \\
      \midrule
      0.2 & 0.8983(10) & 0.8972 & 1.1 \\
      1.0 & 2.0057(10) & 2.0061 & -0.4 \\
      \bottomrule
    \end{tabular}
  \end{threeparttable}
\end{table}
```

A table of five columns or more, or one whose natural width is over about two thirds of the measure, fills the measure instead, so its caption and its rules run the same width:

```latex
\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}} l S[table-format=1.2e2] S[table-format=1.1e2] @{}}
```

- **Width.** A caption wider than its table, with the table centred under it, reads as two objects. Use one of the two forms above.
- **Rules.** `\toprule`, `\midrule` under the heads, `\bottomrule`; `\cmidrule` to group heads over some columns. No vertical rules, no `\hline` grid, no double rules (lint `ruled-table`). White space separates columns. The house style draws the top rule in Prussian like the record strip's, the rules inside in grey and the bottom rule in black, so `\toprule` takes no width of its own.
- **Caption above**, then `\label` (lint `table-caption-below`, `label-before-caption`). The house style sets table captions above with the right skip.
- **Numeric columns** are siunitx `S` columns, which align numbers on the decimal marker. Give each a `table-format` describing its widest entry: `1.4(2)` is one integer digit, four decimals and a two-digit uncertainty. siunitx sizes the column from it under `table-alignment-mode = format`, and the key documents the column under the standard `marker` mode. Wrap non-numeric cells in an `S` column in braces.
- **One format a column.** Every entry in a column has the same number of significant figures, and either every entry is in scientific notation or none is. A column of `1`, `62` and `4.0e6` reads as ragged even when siunitx aligns it; write `1.0e0`, `6.2e1`, `4.0e6`, and siunitx prints the first as `1.0`, since it drops a zero exponent.
- **Heads** with `\colhead{quantity}{unit}`: the quantity in the furniture face at regular weight, and under it the unit in small grey sans, written as siunitx unit macros: `\colhead{$T$}{\second}`. A head with no unit leaves the second argument empty, `\colhead{Model}{}`, which keeps it level with its neighbours. In a head row with no units at all, `\head{...}` sets one line. In an `S` column a head goes in braces so siunitx does not parse it.
- **Grouped heads.** `\spanhead{Measured}` over a `\multicolumn`, with a `\cmidrule(lr)` under it, sets the group's name in tracked Prussian capitals like the record strip's labels.
- **Signed values.** Inside `tabular`, `tabular*` and `tabularx` siunitx sets numbers in maths, so a negative entry keeps its true minus whatever face the cell is in. A column that holds negatives needs the sign in its format: `table-format=-1.1`.
- **Row spacing** is set by the house style, which opens rows by 15 per cent inside every `table`. Group long tables with `\addlinespace` every five rows rather than by rules.
- **Text columns** are left-aligned; a column of prose is an `X` column in `tabularx` at `\linewidth`.

## Rows a reader should find

- `\keyrow` at the start of a row tints it Prussian. Use it for the one row the caption or text points to, such as the adopted model; a second key row makes neither one the key.
- `\band` at the start of alternate rows tints them a light grey. Use it only in a wide table of words, such as a risk register, where the eye loses its row; a table of numbers reads by column and needs no bands.
- `\level{low}`, `\level{medium}` and `\level{high}` set a likelihood or impact as a chip from light to dark grey. Any other word is an error.
- `\badge{H1}` sets a coded tag (a hypothesis, risk or milestone) as a chip that links to the place `\badgetarget{H1}` defines it. `\definebadge{H1}{seriesA}` in the preamble gives a code its colour; a code with no colour is Prussian. Every badge needs one target: without it the link goes nowhere, and `build.py` lists the PDF writer's warning naming `badge.H1`.

## When the table does not fit

`build.py` reports an overfull box when a table runs into the margin, and the rendered page shows it. In this order:

1. Abbreviate heads and move the explanation into the caption or a note under the rule.
2. Reduce `table-format` precision to what the measurement supports.
3. Split one wide table into two, or transpose it.
4. Set it `\small`, never smaller, and only when every table in the document matches.
5. Turn it to landscape with `pdflscape` on a page of its own.

Never `\resizebox` or `\scalebox` round a tabular: the type shrinks to an arbitrary size and the rules thin with it.

## Long tables and text tables

A table longer than a page uses `longtable`, or `xltabular` for `X` columns, which repeat the heads on each page. A table that is mostly sentences is often better as a list or as prose; a work plan with deliverables per row is the exception, and suits `tabularx`.

## On slides and posters

A table on a slide is not a float: it sits under its frame title inside a `center` environment, with no caption or number, and holds at most about five rows. The frame title says what the table shows.
