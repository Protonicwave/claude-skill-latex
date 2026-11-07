# claude-skill-latex

A Claude Code skill that typesets LaTeX documents for physics and computer science: reports, papers, lab reports, notes, slides and posters. It builds every document, reads the log, lints the source and inspects the rendered pages before handing anything back.

## Install

Link the skill folder into Claude Code's skills folder, so edits here take effect without copying. On Windows, in PowerShell:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\latex" -Target "$PWD\skills\latex"
```

On macOS or Linux:

```sh
ln -s "$PWD/skills/latex" ~/.claude/skills/latex
```

The skill's scripts need Python 3.12 or later, a TeX distribution with LuaLaTeX, pdfLaTeX, latexmk and BibTeX, Poppler's `pdftoppm` and `pdfinfo`, and a Perl for latexmk. MiKTeX ships no Perl: on Windows run the scripts from Git Bash, or install Strawberry Perl.

## Development

Requires Python 3.12 or later, [uv](https://docs.astral.sh/uv/) and a TeX distribution with LuaLaTeX and latexmk (MiKTeX or TeX Live).

```sh
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```

Tests marked `tex` build real documents and are skipped when latexmk, pdflatex, lualatex, pdftoppm or pdfinfo is not on `PATH`, or when latexmk does not start (MiKTeX without a Perl).
