---
name: latex
description: Typesets LaTeX documents for physics and computer science to a production standard. Use whenever writing, starting, fixing, restyling or auditing a .tex document, a Beamer talk or poster, or a matplotlib figure meant for LaTeX; whenever a LaTeX build fails, warns or shows overfull boxes, undefined references or citation errors; and whenever the user asks for a report, dissertation, lab report, project plan, paper, lecture notes, slides or poster in LaTeX. Starts new documents from per-profile skeletons in a house style, audits existing ones, respects module templates and journal classes, and hands nothing back until the build, the source lint and a look at the rendered pages are clean. The words themselves belong to /writing and the sources to /research.
---

# LaTeX

Claude acts here as typesetter and production editor. A document is finished when it builds with no defects, the lint reports no defects, every tell has been changed or kept for a stated reason, and the rendered pages have been looked at. Each of the three checks finds faults the others miss: the log knows about overfull lines and undefined references, the lint knows about hyphens in ranges and italic units, and only the rendered page shows a table floating above the section that introduces it.

Generated LaTeX fails in predictable ways. It leaves every design decision to the class defaults (Computer Modern in a narrow column with wide margins), pins floats with `[h]`, draws tables as grids, types units and ranges by hand and never looks at the output. `references/tells.md` lists the patterns; the scripts below catch the mechanical ones.

## Division of labour

- `/writing` owns the words. This skill may change prose only where typesetting requires it: a tie before a reference, a range mark, a quotation mark, a number moved into `\qty`. Rewording a sentence to cure an overfull line is a `/writing` change, so say so when it is the only cure.
- `/research` owns the sources. It hands over a BibTeX file built from verified registry records. Never write a BibTeX entry from memory (`references/bibliography.md`).
- When `/writing` is installed beside this skill, its checker reads LaTeX: `python <skills-dir>/writing/scripts/check.py main.tex --format latex`. Run it on any document whose prose was written or changed in the session.

## Requirements

Python 3.12 or later, a TeX distribution with LuaLaTeX, pdfLaTeX, latexmk and BibTeX (MiKTeX or TeX Live), and Poppler's `pdftoppm` and `pdfinfo` for rendering. The scripts use only the standard library.

latexmk is a Perl script, and MiKTeX ships no Perl. On Windows, run every command below from Git Bash, whose Perl latexmk can use; from PowerShell without a Perl on `PATH`, the build fails with MiKTeX's message "could not find the script engine 'perl'". The same applies to VS Code: LaTeX Workshop builds with latexmk, so it needs Strawberry Perl or Git's `usr/bin` on its `PATH`.

## 1. Read the job and its local rules

Decide first whether the job is a new document or an existing one, then look for rules that outrank the house style, in this order:

1. **A supplied class or template.** A journal class (`revtex4-2`, `iopart`, `IEEEtran`, `elsarticle`), a university thesis class, or a module's template `.tex`. Its design is the specification: keep its class, page layout and fonts.
2. **A module handbook, rubric or brief** in the working folder, or quoted in the template's own text. Page limits, margins, font sizes, sans or serif, line spacing, citation style and required sections are binding. Write each one down with where it came from.
3. **The user's or supervisor's instruction.**
4. **The house style**, `references/design.md`, which applies only where nothing above decides.

A rule found in prose ("margins are 2 cm, the minimal font size is 11 pt") binds as firmly as one in code. When a local rule conflicts with a convention in this skill, the local rule wins and the brief records the conflict. A minimum type size reaches further than the body text: check captions, footnotes, table notes and figure labels against it with the size table in `references/typography.md`, and name in the report any element that falls below it.

## 2. Choose the profile

| Profile | For | Class and engine | Design effort | Read |
|---|---|---|---|---|
| report | project report, dissertation, thesis chapter set | `report` with the house style, LuaLaTeX | moderate | `profiles/report.md` |
| labreport | laboratory or experiment report | `article` with the house style, LuaLaTeX | low | `profiles/labreport.md` |
| notes | lecture, revision or derivation notes | `article` with the house style, LuaLaTeX | moderate | `profiles/notes.md` |
| plan | project plan or proposal, with hypotheses, risks and a Gantt chart | `article` with the house style, LuaLaTeX | moderate | `profiles/plan.md` |
| paper | journal submission or arXiv preprint | the journal's class (REVTeX 4.2 by default), pdfLaTeX | none | `profiles/paper.md` |
| slides | talk, viva, group meeting | Beamer with the Laboratory theme, LuaLaTeX | high | `profiles/slides.md` |
| poster | conference or project poster | Beamer with beamerposter and the LaboratoryPoster theme, LuaLaTeX | high | `profiles/poster.md` |

A document under a module template keeps the template's class and takes the profile only for its content conventions: what goes in each section, how floats, maths and references are set.

## 3. Write the print brief

Before typesetting, write a short brief in the reply. It is the design, so another typesetter could reproduce the document from it.

```
Profile:      which one, and why
Local rules:  each binding rule with its source, or "none found"
Engine:       LuaLaTeX or pdfLaTeX, and why
Type:         text, maths, furniture (headings, captions, table heads) and code faces
Page:         paper, measure, margins, columns, line spacing
Citations:    style, bibliography file, who supplies the entries
Figures:      medium overlay, widths, who draws them
Signature:    the house record strip, or "none" under a template or journal
```

Scale it to the job: two or three lines for a fix to a lab report, every line for a new report or poster. Under a supplied template most lines read "template", which is the point. Then attack it with the questions in `references/design.md` (could this be any LaTeX document? does every face have a matching maths face?) and revise.

## 4. Typeset

**New document.** Scaffold it, then replace the example content and keep the conventions:

```
python <skill-dir>/scripts/new_project.py PROFILE FOLDER
```

It writes `main.tex` (with `chapters/` for a report, and for a plan the Gantt chart and `figures/gantt.py`, which redraws it from a table of tasks), `refs.bib`, the house packages, `figures/pendulum.pdf` with the matching `.mplstyle` files and the figure helper `laboratory.py`, a `latexmkrc` that sets the engine and the `build/` folder, and `.vscode/settings.json` for LaTeX Workshop. It refuses, writing nothing, if any file it would write already exists. That includes a `refs.bib` that `/research` has already written: scaffold first, or move the file aside and put it back after. Each skeleton's comments state the convention for its element.

**Existing document.** Audit before changing anything: build, lint and render as in step 5, and report the findings ranked by what a reader would notice first. Fix defects. Change a tell where the house style or a local rule calls for it; leave a choice the author or the template made deliberately, and say so. Change only what a finding requires: no reformatting of the whole file, no reordering of the preamble for taste. If the document has its own build script, read it for the engine and the bibliography tool and pass the matching `--engine`. Build the document where it lives, since documents often include files from outside their folder (`../../results/figure.pdf`); if its folder already holds the author's own build output, pass `--outdir` with an absolute path in a temporary folder so the audit leaves that output untouched.

While typesetting, follow the reference for each element:

- maths, operators, units and uncertainties: `references/maths.md`;
- text, dashes, quotes, ties, emphasis and overfull lines: `references/typography.md`;
- figures and the matplotlib workflow: `references/figures.md`;
- tables: `references/tables.md`;
- citations and the bibliography: `references/bibliography.md`;
- files, labels, cross-references, package order and the house macros: `references/structure.md`.

## 5. Build, lint and look

Run the loop until it is clean. `<skill-dir>` is this skill's folder; every command takes paths with spaces.

```
python <skill-dir>/scripts/build.py main.tex [--engine pdflatex] [--timeout-seconds 600]
python <skill-dir>/scripts/lint.py main.tex
python <skill-dir>/scripts/render.py build/main.pdf [--pages 1,3-5] [--dpi 110]
```

- **build.py** runs latexmk into `build/` and reads the log. Without `--engine`, the project's `latexmkrc` chooses the engine, as it does for an editor; a scaffolded project needs no option. Every run is a full build, and output an earlier build left behind is ignored. Exit 0 means no defects; 1 means defects or a failed build; 2 means a bad argument or latexmk not found. Defects are errors, overfull boxes over 1 pt, underfull boxes at badness 10000, undefined or multiply defined references and citations, missing glyphs, font substitutions and BibTeX errors, each with file and line. Warnings are judged. Errors come first in the report: a build stopped by an error leaves every later reference and citation undefined, so fix the error and rebuild before reading the rest. When latexmk fails before TeX runs, the report quotes latexmk's own explanation, such as a missing Perl. The first build of a new document can take minutes while MiKTeX installs packages; the default timeout allows for it.
- **lint.py** reads the source, following `\input`, `\include` and `\subfile`. Defects (exit 1) are wrong in any document. Tells are judged: change each one, or keep it and say why in the report. Under a supplied class it counts house-style tells as suppressed rather than reporting them. Its output ends with a glossary of the rules it found, each with its fix.
- **render.py** writes one PNG per page to `build/pages/`. Read the images. For a long document, look at the title page, every page that holds a float, a table or display maths you changed, and the last page.

Look at each page for what neither script can see:

- a float above the text that first refers to it, or above its own section heading;
- a page of floats alone, or a large gap where a float would not fit;
- a heading alone at the foot of a page, or one line of a paragraph alone at the top or foot;
- type in a figure much larger or smaller than the text, or labels colliding with data;
- a table wider than the measure, or a table scaled down to fit;
- on slides, text below the frame's foot or a frame of more than about 40 words; on a poster, a column that ends far above the others.

Check the page count against any limit in the local rules with `pdfinfo build/main.pdf`, and count the pages the rule counts (a limit that excludes the bibliography excludes those pages).

Fix the cause rather than the symptom: a float in the wrong place moves in the source, not under `[H]`; an overfull line is cured in the order `references/typography.md` gives, never with `\sloppy`.

## 6. Report

State what was run and what each check produced (build counts, lint counts, pages looked at), what changed and why, every tell kept with its reason, every local rule and whether the document meets it, and anything not verified, such as a page limit that depends on how the marker counts. Leave the PDF in `build/`.

## Files

- `profiles/`: one file per profile, with its sections, conventions and checks.
- `references/design.md`: the method, the house style and how far to apply it.
- `references/tells.md`: the patterns of generated LaTeX, including those only the rendered page shows.
- `references/typography.md`, `references/maths.md`, `references/figures.md`, `references/tables.md`, `references/bibliography.md`, `references/structure.md`: the conventions by element.
- `scripts/build.py`, `scripts/lint.py`, `scripts/render.py`, `scripts/new_project.py`: the loop and the scaffolder.
- `assets/`: the house packages, Beamer themes, matplotlib styles, latexmkrc, VS Code settings and skeletons that `new_project.py` copies.

The sources behind the rules and the specimens the house style was chosen from are in the `research/` folder of the repository this skill is published from.
