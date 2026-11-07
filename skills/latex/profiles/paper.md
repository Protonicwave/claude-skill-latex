# Paper

A journal submission or arXiv preprint. The journal owns the design, so design effort is none: the class sets type, layout and references, and this skill applies only the conventions the class leaves to the author.

## Setup

- REVTeX 4.2 for the APS journals: `\documentclass[aps,prb,reprint]{revtex4-2}`, changing `prb` to the target journal. For another publisher, start from that journal's own template, not from this skeleton.
- pdfLaTeX, as the journals and arXiv expect. No house style, no OpenType fonts, no `laboratory.sty`.
- The skeleton loads only `graphicx`, `booktabs`, `siunitx`, `hyperref` with `hidelinks`, and `cleveref` with `capitalise`, and defines `\dd`. Add packages only when the content needs them, and check the journal's list of accepted packages.
- Figures use the `journal` mplstyle overlay: 86 mm wide, 8 pt Computer Modern, panels stacked, typeset by pdfLaTeX.

## Conventions

- `\cref` prints "Fig. 1" and "Eq. (1)" mid-sentence and spells them out at the start of one, as APS asks.
- The bibliography comes from `apsrev4-2`, which REVTeX loads; the document gives only `\bibliography{refs}`.
- The abstract goes before `\maketitle` in REVTeX.
- Full-width floats in a two-column layout use `figure*` and `table*`.
- REVTeX's `ruledtabular` environment draws the double rules of the APS journals' own tables, and APS's REVTeX guide asks for it "whenever possible". Under the journal class that is the journal's design, so it overrides booktabs' rule against double rules; the skeleton's booktabs table is for a journal that does not ask.

## Expected warnings

The REVTeX skeleton builds with two warnings that come from the class, not the document: nameref's note about REVTeX's `\label`, and apsrev4-2's note about its `jnrlst` control entry. Report them as expected; any other warning is judged as usual.

## Checks for this profile

- arXiv does not run BibTeX, so an arXiv upload carries the `.bbl` from `build/`, renamed to match the main file and placed beside it.
- Every figure PDF embeds its fonts; the pgf backend does this.
- The journal's length rules (words, figures, references) are local rules for step 1.
