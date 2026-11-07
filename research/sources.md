# Sources behind the rules

Every source below was opened and read on 2026-11-07, and every quotation is copied from it. Package manuals were read from the copies MiKTeX installs, which match the CTAN versions named; papers were checked against their Crossref or OpenAlex records. A claim the sources did not support was corrected in the skill or dropped; those cases are listed at the end.

## Which rule rests on which source

| Rule in the skill | Where | Source |
|---|---|---|
| No vertical rules, no double rules, units in the column head | `tables.md` | booktabs [1]; APS style guide [9] for units in heads |
| `S` columns align on the decimal marker; `\qty`, `\num`, `\unit`, `\qtyrange`, `\qtylist` | `tables.md`, `maths.md` | siunitx [2] |
| `$$`, `eqnarray`, `\bf`, `center` in floats and the listed packages are obsolete | `maths.md`, `tells.md`, lint | l2tabu [3] |
| Variables italic; descriptive subscripts, the differential, e and units upright | `maths.md`, lint | NIST SP 811 [4]; Beccari [5] for the imaginary unit |
| APS accepts the differential, e and i upright or italic | `maths.md` | APS style guide [9] |
| Float defaults; place a float after the paragraph that first refers to it; `flafter` | `design.md`, `figures.md`, house style | Mittelbach [6]; APS REVTeX guide [8] |
| Protrusion and expansion; which engines support them | `typography.md` | microtype [7] |
| fontspec sets the TU encoding, so `[T1]{fontenc}` switches text back | `tells.md`, lint | fontspec [10] |
| inputenc does nothing under LuaLaTeX | lint | `inputenc.sty` [11] |
| unicode-math after other maths and font packages; `\setmathfont` | `structure.md` | unicode-math [12] |
| hyperref last, `\texorpdfstring` for bookmarks; cleveref after hyperref | `structure.md` | hyperref [13]; cleveref [14] |
| apsrev4-2 with natbib; numbered citations in square brackets in order of appearance | `bibliography.md` | REVTeX guide [8]; APS style guide [9] |
| `ruledtabular` under REVTeX | `profiles/paper.md` | APS REVTeX guide [8] |
| Draw a figure for its medium; no default colour maps | `figures.md` | Rougier et al. [15] |
| Rainbow maps distort data and fail readers with colour-vision deficiency | `figures.md` | Crameri et al. [16] |
| A frame title states the frame's claim as a sentence | `profiles/slides.md` | Garner and Alley [17] |
| About 40 words on a frame; `aspectratio=169` | `SKILL.md`, `profiles/slides.md` | Beamer user guide [18] |
| No underlining; one space between sentences; 45 to 90 characters a line | `typography.md`, `design.md` | Butterick [19] |
| The figure workflow through the pgf backend | `figures.md` | matplotlib [20] |
| latexmk is a Perl script and MiKTeX ships no Perl | `SKILL.md` | latexmk [21]; MiKTeX [22] |
| LaTeX Workshop builds with latexmk and finds the output folder | `structure.md` | LaTeX Workshop [23] |
| Hyphen, en dash, em dash and minus; ties | `typography.md` | lshort [24] |
| Type sizes of the 11 and 12 pt class options | `typography.md` | `size11.clo` and `size12.clo` [11] |

## The sources

[1] S. Fear, "Publication quality tables in LaTeX", booktabs documentation v1.61803398 (2020), maintained by D. Els. https://ctan.org/pkg/booktabs. Section 2, p. 3: "1. Never, ever use vertical rules. 2. Never use double rules." and "3. Put the units in the column heading (not in the body of the table)."

[2] J. Wright, "siunitx: A comprehensive (SI) units package", v3.6.4 (2026). https://ctan.org/pkg/siunitx. Section 3.9, p. 18: "Aligning numbers in tabular content is handled by a new column type, the S column." Section 4.13, p. 58: "With the standard setting, marker, the package centers the decimal marker in a tabular column". p. 61: under `table-alignment-mode = format`, table-format "defines the space to reserve for a number". Sections 3.1 and 3.4 define `\num`, `\unit`, `\qty`, `\numrange`, `\qtylist` and `\qtyrange`.

[3] M. Trettin, trans. J. Fenn, "An essential guide to LaTeX2e usage: Obsolete commands and packages", English version 1.8.5.7 (2007). https://ctan.org/pkg/l2tabu-english. Section 1.6, p. 6, on `$$`: "It will modify vertical spacing within formulae, rendering them inconsistent." Section 3.3, p. 15: "you should never use the displaymath, eqnarray, or eqnarray* environments". Section 3.1, p. 14: "\centering instead of \begin{center} ... because the latter will include an additional vertical skip". Section 2 lists a4wide, epsfig, doublespace, fancyheadings, times, palatino and pslatex as obsolete, with replacements. The guide dates from 2007, so it is cited only for what is obsolete, not for every replacement it names.

[4] A. Thompson and B. N. Taylor, "Guide for the Use of the International System of Units (SI)", NIST Special Publication 811 (2008). https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication811e2008.pdf. Section 10.2, p. 34: "symbols for quantities and variables: italic; symbols for units: roman; symbols for descriptive terms: roman", and "a subscript or superscript on a quantity symbol is in roman type if it is descriptive". Section 10.2.3, p. 35, sets in roman "symbols representing mathematical constants that never change (for example, π)" and "well defined operators", listing the differential d and e, the base of natural logarithms.

[5] C. Beccari, "Typesetting mathematics for science and technology according to ISO 31/XI", TUGboat 18(1), 39-48 (1997). https://tug.org/TUGboat/tb18-1/tb54becc.pdf. Section 2.2, p. 40: numerical constants in roman apply "to e = 2.718 281 8 ..., the base of natural logarithms, to the 'imaginary unit'". p. 41: "the operator of differentiation, should be set in roman type".

[6] F. Mittelbach, "How to influence the position of float environments like figure and table in LaTeX?", TUGboat 35(3), 248-254 (2014). https://tug.org/TUGboat/tb35-3/tb111mitt-float.pdf. Section 3.4 gives the defaults \topfraction 0.7, \bottomfraction 0.3, \textfraction 0.2, \floatpagefraction 0.5, topnumber 2, which `article.cls` sets. Section 4.1, p. 251: "normally a float is placed in the source near its first call-out ... because this will ensure that the float appears either on the same page as this text or on a later page." Section 6.3: placing floats strictly after the call-out "is implemented by the flafter package".

[7] R. Schlicht, "The microtype package", v3.2d (2026). https://ctan.org/pkg/microtype. Abstract: "character protrusion requires pdfTeX ..., LuaTeX, or XeTeX ... Font expansion works with pdfTeX ... or LuaTeX."

[8] American Physical Society, "REVTeX 4.2 Author's Guide" and "APS Author Guide for REVTeX 4.2" (December 2018), in https://ctan.org/pkg/revtex. Author's Guide, section VIII: natbib is required, and "apsrev4-2.bst (APS journals using a numeric citation style, i.e., all but RMP)". APS guide, section VII.2: "Figures should be placed as close as possible to the point where they are first referenced". Section VIII.1: "REVTeX 4.2 provides the ruledtabular environment which automatically puts the scotch rules (double lines) around tables ... This environment should be used whenever possible."

[9] American Physical Society, "APS Journals Style Guide for Authors" (November 2024). https://res.cloudinary.com/apsphysics/image/upload/v1715884920/aps-journals-style-guide_tnoyln.pdf. Section II.G.2.a, p. 15: references "should be designated by online arabic numerals enclosed in square brackets and should be numbered consecutively in order of their first appearance in text." Section III.D, p. 53: units "are set in roman font". Section II.R.4, p. 36: "Quantities that appear in the headings should be followed by units, given in parentheses." Section IV.A.1.b, p. 56, lists "Derivatives and differentials: d, dx, dt (or d, dx, dt)", "Imaginary unit i (or i)" and "exponential e (or e)", with the alternative in italic. A February 2026 edition carries the same references wording.

[10] W. Robertson et al., "The fontspec package", v2.9h (2026). https://ctan.org/pkg/fontspec. Section 3.1, p. 6: "The package switches the NFSS font encoding to TU." The manual does not forbid loading fontenc; lint's rule rests on the consequence that `[T1]{fontenc}` switches the text back to a legacy encoding.

[11] The LaTeX Project, LaTeX kernel and base files as installed by MiKTeX (format 2026-06-01). `inputenc.sty` issues "inputenc package ignored with utf8 based engines". `size11.clo` and `size12.clo` set the sizes in `typography.md`.

[12] W. Robertson et al., "The unicode-math package", v0.8r (2023). https://ctan.org/pkg/unicode-math. Section 3, p. 4: "It should be loaded after any other maths or font-related package in case it needs to overwrite their definitions."

[13] S. Rahtz, H. Oberdiek and The LaTeX Project, "Hypertext marks in LaTeX: a manual for hyperref", v7.01s (2026). https://ctan.org/pkg/hyperref. Section 3, p. 6: "Make sure it comes last of your loaded packages". Section 6.1.2, p. 29: bookmark text cannot hold maths, hence `\texorpdfstring{TeXstring}{PDFstring}`. Section 11.1 lists the exceptions.

[14] T. Cubitt, "The cleveref package", v0.21.4. https://ctan.org/pkg/cleveref. Section 14.1, p. 25: "The packages must be loaded in the following order: varioref, hyperref, cleveref."

[15] N. P. Rougier, M. Droettboom and P. E. Bourne, "Ten Simple Rules for Better Figures", PLoS Comput. Biol. 10, e1003833 (2014). doi:10.1371/journal.pcbi.1003833. Crossref record matches; no retraction or correction found. Rule 3: "Ideally, each type of support medium requires a different figure, and you should abandon the practice of extracting a figure from your article to be put, as is, in your oral presentation." Rule 6: "Do not use the default colormap (e.g., jet or rainbow) unless there is an explicit reason to do so".

[16] F. Crameri, G. E. Shephard and P. J. Heron, "The misuse of colour in science communication", Nat. Commun. 11, 5444 (2020). doi:10.1038/s41467-020-19160-7. Crossref record matches; no retraction or correction found. Introduction: a colour map built on a physical rather than perceptual basis "adds artificial boundaries to some parts of the data range, hiding small-scale variations elsewhere ... and renders the data unreadable for readers with common colour-vision deficiencies".

[17] J. K. Garner and M. P. Alley, "How the Design of Presentation Slides Affects Audience Comprehension: A Case for the Assertion-Evidence Approach", Int. J. Eng. Educ. 29, 1564-1579 (2013). No DOI; OpenAlex W2738564864 matches. Section 1.4: "the assertion-evidence slide structure calls for a sentence headline that makes explicit the main message or assertion". Abstract: the assertion-evidence group showed "superior comprehension and fewer misconceptions".

[18] T. Tantau, J. Wright and V. Miletić, "The beamer class: User Guide for version 3.78" (2026). https://ctan.org/pkg/beamer. Section 5.1.3, p. 33: "A usual frame should have between 20 and 40 words. The maximum should be at about 80 words." Section 8.3, p. 75: `aspectratio=169` "Sets aspect ratio to 16:9".

[19] M. Butterick, "Butterick's Practical Typography", web book, read 2026-11-07. https://practicaltypography.com/line-length.html: "Aim for an average line length of 45-90 characters, including spaces." https://practicaltypography.com/underlining.html: "In a printed document, don't underline. Ever." https://practicaltypography.com/one-space-between-sentences.html: "Always put exactly one space between sentences."

[20] Matplotlib development team, "Text rendering with XeLaTeX/LuaLaTeX via the pgf backend", Matplotlib 3.11.2 documentation. https://matplotlib.org/stable/users/explain/text/pgf.html. Documents `pgf.texsystem` ('xelatex', 'lualatex' or 'pdflatex'), `pgf.preamble`, `pgf.rcfonts`, and "plt.savefig('figure.pdf', backend='pgf')".

[21] J. Collins, latexmk v4.88 (9 March 2026), man page, README and INSTALL. https://ctan.org/pkg/latexmk. README: "Latexmk is a perl script." INSTALL: with MiKTeX "you will also need to install a distribution of Perl if you haven't done so already." The man page documents `$out_dir`, `$pdf_mode` and `-g`.

[22] MiKTeX knowledge base, "Fix: script engine not found". https://miktex.org/kb/fix-script-engine-not-found: "Script engines like perl.exe are not part of the MiKTeX distribution. You have to install them manually."

[23] J. Yu and contributors, LaTeX Workshop wiki, "Compile", and `package.json` of version 10.20.0. https://github.com/James-Yu/LaTeX-Workshop/wiki/Compile: "By default latexmk is used. This tool is bundled in most LaTeX distributions, and requires perl to execute." With `latex-workshop.latex.outDir` at its default, the extension reads the output folder from latexmk's `-outdir`.

[24] T. Oetiker, H. Partl, I. Hyna and E. Schlegl, "The Not So Short Introduction to LaTeX 2ε", version 6.4 (2021). https://ctan.org/pkg/lshort-english. Section 2.4.2, p. 20: "LaTeX knows four kinds of dashes", with `pages 13--67` as the en dash's example and the minus sign as the fourth. Section 2.6, p. 27: a tilde "prohibits a line break", as in `cf.~Fig.~5`.

## Claims corrected or not supported

- **Line length.** The skill first set the house measure against "the 45 to 75 characters book typography recommends", which is Bringhurst's figure. No readable copy of Bringhurst was found, only secondary quotations, so the skill now cites Butterick's 45 to 90, which was read.
- **subfigure.** l2tabu does not mention it. lint still lists it as obsolete with subcaption as the replacement, on the strength of its CTAN status, which was not checked here; the skill's text no longer cites it as an example.
- **fontenc.** fontspec does not forbid loading fontenc; one of its own examples loads `[T1]{fontenc}` deliberately. The lint rule stands on the encoding switch, not on a prohibition.
- **ISO conventions and the journals.** APS accepts italic or upright d, e and i, so the skill no longer says the physics journals follow ISO 80000-2.
- **A lone `[h]`.** Mittelbach does not discuss it; the LaTeX kernel changes it to `[ht]` with a warning. The skill makes no claim that rests on either.
- **Table captions above.** No source read here places table captions above the table. It stays as a house convention, stated without a citation.
- **Frame titles as sentences.** The Beamer guide asks for informative titles but gives noun phrases as examples; the sentence-headline rule rests on Garner and Alley.
