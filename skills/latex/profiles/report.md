# Report

A project report, dissertation or thesis-length document with chapters. Readers are an examiner who reads it end to end and a second marker who navigates by the contents page, so structure and cross-references carry as much weight as the page.

## Setup

- `report` class at 11 pt with `\usepackage{laboratory}`, built with LuaLaTeX.
- `main.tex` holds the title fields, abstract, contents and the `\include` of each chapter from `chapters/`. The skeleton has introduction, method, results and conclusions; add chapters as files, not as sections of `main.tex`.
- Under a department's thesis class or template, keep that class and take only the conventions below.

## Sections and what each holds

| Part | Holds |
|---|---|
| Title and record strip | Title, author, date, `\source` pointing at the repository behind the work |
| Abstract | Aim, method, main result with its uncertainty, and what it means, in one paragraph |
| Contents | `\tableofcontents`; links stay black so the page does not drown in the accent |
| Introduction | The question, why it matters, and a closing sentence that maps the chapters by `\cref` |
| Method or theory chapters | Model, derivations, apparatus or code, with numbered equations the results refer back to |
| Results | Each result first, then the figure or table that shows it |
| Conclusions | What was found, how far to trust it, what would test it further |
| References | `\bibliography{refs}` with `apsrev4-2`, titled "References" by the house style |
| Appendices | after `\appendix`: code listings, extra data, derivations the argument does not need |

## Checks for this profile

- Every chapter opens on a new page; a chapter opening should not be followed by a float before any text.
- A figure or table appears in the chapter whose text refers to it, after the reference.
- The contents page shows no more than three levels.
- Running heads carry the title; check it is short enough to fit on one line at the head of the page.
- Page count against any limit, counting only the pages the rule counts.
