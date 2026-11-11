# Design

A LaTeX document looks generated when nobody decided anything: the class supplied the face, the margins, the heading sizes and the float rules, and the result could belong to any student in any year. A well-made document is the opposite. A few decisions are made once, written down in a style file, and applied everywhere, and the effort goes where the reader will notice it.

## Effort follows the profile

| Situation | Effort | What that means |
|---|---|---|
| Journal class (REVTeX, IOP, IEEE, Elsevier) | none | The journal owns the design. Apply the conventions for maths, units, floats, tables and references, and nothing else. |
| Module or university template | inside the template | Keep its class, layout and fonts. Improve only what it leaves open: units, maths, tables, figures, references, float placement. |
| Lab report | low | The house style as the skeleton has it. Spend the effort on figures and tables. |
| Report, notes | moderate | The house style, with care over chapter openings, figures drawn for the page and a contents page that reads well. |
| Slides, poster | high | Every frame or block composed by eye; figures redrawn for the medium. |

## Attack the brief

Before building, ask of the brief in `SKILL.md`:

- **Could this be any LaTeX document?** If the face is Computer Modern, the margins are the class defaults and the title is the centred `\maketitle`, nothing has been decided. Under a template that answer is correct; anywhere else it is a tell.
- **Does every text face have a maths face drawn to match?** A sans document with serif maths, or Palatino text with Computer Modern maths, puts two designs in every line that holds a symbol. The pairings below all match.
- **Is there one accent?** One colour for headings, links and the data series that matters. A second accent dilutes the first.
- **Is there one signature, and only one?** The house signature is the record strip under the title. A document needs no second ornament.
- **Does each choice trace to the reader, the medium or a local rule?** A poster face is chosen for two metres; a journal figure for an 86 mm column.

## The house style: Laboratory

Chosen by the user from rendered specimens (`research/house-style.md` in the repository). `laboratory.sty` sets it for the `article` and `report` classes; `beamerthemeLaboratory.sty` and `beamerthemeLaboratoryPoster.sty` set it for slides and posters. Do not restate these settings in a document's preamble.

| Element | Setting |
|---|---|
| Text and maths | Erewhon and Erewhon Math at 11 pt, scaled to 0.95 |
| Furniture | Source Sans 3 for headings, captions, table heads, running head, record strip, theorem heads |
| Code | IBM Plex Mono, scaled to the text's x-height, in a listing with a Prussian rule at the left |
| Accent | Prussian blue `#1F4A73`: heading numbers, caption labels, links, the first data series |
| Page | A4, 150 mm by 232 mm text block centred with 30 mm side margins, running head with the title on the left and the page number on the right |
| Title | Left-aligned sans title, then the record strip: a Prussian rule, author, date and source, a grey hairline; the abstract below it indented 2 em on both sides |
| Short report | The `compact` option runs the contents and each chapter on without a page break, with a float barrier before each chapter so no float drifts into the next one |
| Floats | `[tbp]` with relaxed fractions so two floats can share a page with text; `flafter` keeps each float below the point where it is written, so a float written after its first mention stays after it |
| Captions | Small sans, label in Prussian followed by an en space; tables captioned above, figures below |
| Tables | booktabs rules, regular-weight sans heads, rows 15 per cent further apart than the class sets them; a table either fills the measure or holds its caption to its own width |
| Figures | `laboratory.mplstyle`: Erewhon and Erewhon Math through LuaLaTeX, 9 pt, bold panel labels, Prussian, near black and 45 per cent grey |
| Spacing | `\frenchspacing`, `\emergencystretch` of 1.5 em, microtype |

The measure is 150 mm, about 95 characters a line at 11 pt. That is still wider than the 45 to 90 Butterick allows for body text, and narrower than the 175 mm the house style first used. The user chose 150 mm on 11 November 2026 after reading pages set at 175 mm, finding the long line hard to track back to the start of the next. Keep it; do not narrow a house document further to the textbook range, and do not widen it.

## A different look

When the user asks for a different face, change the house style's font lines, not each document, and keep every pairing matched. LuaLaTeX with `fontspec` and `unicode-math`:

| Text | Maths | Character |
|---|---|---|
| Erewhon | Erewhon Math | the house face: Utopia's descendant, open and even |
| STIX Two Text | STIX Two Math | the journal face; reads as a physics paper |
| TeX Gyre Pagella | TeX Gyre Pagella Math, or Euler Math | Palatino's calligraphic warmth; Euler for a mathematical text |
| Libertinus Serif | Libertinus Math | narrow and literary, economical on long reports |
| EB Garamond | Garamond Math | old-style and light; for notes rather than data-heavy work |
| New Computer Modern | New Computer Modern Math | Knuth's face in OpenType, when the module expects the LaTeX look |
| Fira Sans | Fira Math | sans text with sans maths: the pairing for a template that demands sans serif |

Source Serif 4 and IBM Plex Sans are installed but have no maths face drawn for them, so they are not used as text faces in documents with mathematics. Source Sans 3 has none either, which is why it serves only as furniture.

Under pdfLaTeX, as a journal class or arXiv requires, fonts come from the class or from Type 1 packages; the class decides, and a paper adds none.

A module template that asks for sans serif under pdfLaTeX usually sets `\renewcommand{\familydefault}{\sfdefault}`, which gives Computer Modern Sans text with Computer Modern serif maths. `\usepackage{sansmathfonts}` supplies maths in the same sans design. Propose it as a fix to a tell rather than impose it, since the template owns the fonts, and rebuild afterwards: in a document that asks for the `b` series it reports a bold font substitution, which `build.py` lists as a defect to judge.

## Defects and tells

The scripts sort findings in two kinds, and so does any review by eye.

- A **defect** is wrong in any document: an undefined reference, an overfull line, a hyphen joining a range, an italic unit. Fix every one.
- A **tell** is a habit of unconsidered or generated LaTeX: `[h]` on every float, vertical rules, Computer Modern by default, a figure drawn at one size and scaled to another. Change it, or keep it and give the reason in the report. A tell kept for a reason (a template's `\hline` tables, a module's demand for underlining) is a decision, not a fault.
