# Lab report

A report on one experiment, marked against a rubric. The reader wants the result, its uncertainty and the evidence, quickly. Design effort is low: the house style as the skeleton sets it, with care spent on the figure and the table.

## Setup

- `article` class at 11 pt with `\usepackage{laboratory}`, built with LuaLaTeX.
- One file, `main.tex`. No contents page.
- A module's lab report template replaces the house style; its rubric's section list replaces the one below.

## Sections and what each holds

| Section | Holds |
|---|---|
| Abstract | Four sentences: aim, method, main result with its uncertainty, what it means |
| Introduction | What is measured, why, and the model the measurement tests, with its source |
| Theory | The model's equations, numbered where the results use them |
| Method | Apparatus, procedure, and how each uncertainty was estimated |
| Results | The result first, then the figure and table that support it, then the fit statistics |
| Discussion | What the result means, how far to trust it, the largest systematic error and how to bound it |
| Conclusion | The result and its uncertainty in one or two sentences |
| References | `apsrev4-2` unless the module names a style |

Two heading levels at most.

## Checks for this profile

- The main result appears in the abstract, the results and the conclusion with the same value, uncertainty and unit.
- Every measured number has its unit through siunitx and an uncertainty where one exists.
- The figure shows residuals under any fit, and its caption says what the error bars are.
- The table's columns align on the decimal marker and give units in the heads.
- Page count against the rubric's limit.
