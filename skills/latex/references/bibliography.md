# Citations and bibliography

## Who supplies what

Every bibliography entry comes from a registry record retrieved in the session: `/research` builds the BibTeX file from verified records, and `/writing`'s `sources.md` gives the rules. This skill typesets citations; it never writes, completes or repairs an entry from memory. An entry that is missing, or that BibTeX reports as incomplete, goes back to `/research`, and the report lists it.

## The default: APS numeric with BibTeX

```latex
\usepackage[numbers,sort&compress]{natbib}   % the house style loads this
...
\bibliographystyle{apsrev4-2}
\bibliography{refs}
```

References are numbered in order of first citation and cited in square brackets. `sort&compress` sorts the numbers in one citation and joins a run of three or more into a range. `apsrev4-2` comes with REVTeX 4.2 and works outside it with natbib.

Use another style only when a rule asks for it:

| Situation | Setup |
|---|---|
| A module handbook or template names a style | That style, exactly as named |
| A computing module | IEEE: `\bibliographystyle{IEEEtran}`, with `cite` instead of natbib |
| IOP Harvard requested | the author-year style the IOP template supplies, with natbib's `authoryear` option |
| A journal class | the class's own setup; REVTeX loads natbib and `apsrev4-2` itself |

BibTeX with natbib is the default because `/writing` and `/research` produce for it. Do not switch a document to biblatex and biber unless the user asks.

## Citing

- `\cite{key}` with a tie before it: `as shown~\cite{nelson1986}` (lint `breakable-reference`).
- Several sources at one point in one command: `\cite{a,b,c}`, never `\cite{a}\cite{b}` (lint `split-citation`).
- A citation is not a noun. Write "Nelson and Olsson~\cite{nelson1986} measured", not "\cite{nelson1986} measured".
- A figure or table taken from a source cites it in the caption.

## The BibTeX file

- One file, `refs.bib`, beside `main.tex`. build.py and the house latexmkrc tell BibTeX to look there even though it runs in `build/`.
- Keys are stable and readable: `nelson1986`, `taylor1997`.
- Protect capitals the style must keep with braces in the title field: `{Ising}`, `{Monte Carlo}`, `{RF}`.
- Undefined citations and BibTeX errors are defects in `build.py`'s report. A warning that an entry lacks a field is judged: a missing volume for a book is fine, a missing journal is not.

## Converting a hand-made bibliography

A template's `thebibliography` with `\bibitem` entries is converted to BibTeX when the template allows it, by looking up each entry through `/research`, never by transcribing the visible fields. An entry that cannot be verified keeps a visible `[UNVERIFIED: ...]` marker in the source comment and in the report. If the template requires `thebibliography`, keep it and set each entry to the template's pattern.
