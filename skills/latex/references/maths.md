# Mathematics, numbers and units

The conventions follow ISO 80000-2 as NIST's guide to the SI states it: a symbol's typeface carries its meaning. The APS journals accept the differential, e and i either upright or italic, so under a journal class the journal's own practice decides. The sources are in `research/sources.md` in the repository.

## Typeface carries meaning

| Kind | Face | Source |
|---|---|---|
| Variables and physical quantities: $T$, $L$, $\theta$ | italic | default in maths |
| Vectors and matrices | bold italic | `\symbf{r}` under unicode-math, `\boldsymbol{r}` under pdfLaTeX |
| Descriptive subscripts and superscripts: max, eff, fit | upright | `T_\mathrm{fit}`; lint `italic-subscript-label` catches common ones such as max and eff, not every word |
| Index subscripts that are variables: $i$, $n$ | italic | `x_i` |
| Functions and operators | upright | `\sin`, `\exp`, `\operatorname{erf}`, or `\DeclareMathOperator` in the style |
| The differential | upright | `\dd t` (house macro); lint `italic-differential` |
| The exponential constant and the imaginary unit | upright | `\mathrm{e}`, `\mathrm{i}`; lint `italic-constant-e` |
| Units | upright | always through siunitx |
| Numbers | upright | default |
| Words inside maths | upright text | `\text{if}` |

The elementary charge $e$ is a quantity and stays italic; the exponential constant is upright. In a document that already sets e and i italic throughout, consistency wins over correcting half of them: report it as a tell.

## Displays

- `equation` for one line, `align` for several aligned on a relation, `multline` or `split` for one equation too long for the measure, `gather` for several centred. Never `$$ ... $$` or `eqnarray`, which space wrongly.
- A display is part of its sentence. End it with the comma or full stop the sentence needs, and continue the sentence after it without a blank line. A blank line before a display starts a new paragraph and leaves an empty line above the equation (lint `blank-line-before-display`).
- Number the displays the text refers to; use `equation*` or `\notag` for the rest. Refer to them with `\cref{eq:period}`, which prints "Equation (2)" in the house style.
- Do not start a sentence with a symbol, and separate two formulas with words.

## Inline maths

- A stacked `\frac` in running text squeezes the line and pushes its neighbours apart (lint `inline-fraction`). Write $L/g$ inline, or display the expression.
- `\times` for multiplication of numbers and for dimensions (`$32 \times 32$`), `\cdot` sparingly for a product that needs a visible mark.
- `\left` and `\right` only around tall content; they oversize brackets round single symbols.

## Numbers and units

Every number with a unit goes through siunitx, which sets the unit upright, puts a thin space before it and formats uncertainty and exponents consistently.

| Write | Source |
|---|---|
| 9.809(4) m s⁻² | `\qty{9.809(4)}{\metre\per\second\squared}` |
| 1.7 × 10⁻⁴ | `\num{1.7e-4}` |
| a bare unit in a column head | `\unit{\metre}` |
| 0.2 m to 1.0 m | `\qtyrange{0.2}{1.0}{\metre}` |
| 0.2 and 1.0 m | `\qtylist{0.2;1.0}{\metre}` |
| an angle of 3° | `\qty{3}{\degree}` |

The house style groups digits only from five figures (`group-minimum-digits = 5`), so 1000 stays whole and 10 000 is grouped. Uncertainty is given in brackets on the last digits, `9.809(4)`, which reads as 9.809 ± 0.004.

Quote an uncertainty to one or two significant figures and the value to the same decimal place. That is a content rule; a mismatch found while typesetting goes in the report for `/writing`.

## unicode-math and the house macros

Under LuaLaTeX the house style loads `unicode-math`, so mathematical alphabets are `\symbf`, `\symup`, `\symsf` and `\symcal`. Older `\mathbf` still works for upright bold letters. `\boldsymbol` and `bm` are pdfLaTeX tools; under unicode-math use `\symbf`.

The house style defines:

- `\dd`, the upright differential with a thin space before it: `\frac{\dd^2\theta}{\dd t^2}`, `\int f(x) \dd x`.
- A tighter maths slash for Erewhon Math, so $J/k$ does not read as $J\ /\ k$. It is automatic.

A REVTeX paper has no house style, so its skeleton defines `\dd` itself.
