# claude-skill-latex

A Claude Code skill that typesets LaTeX documents for physics and computer science: reports, papers, lab reports, notes, slides and posters. It builds every document, reads the log, lints the source and inspects the rendered pages before handing anything back.

## Development

Requires Python 3.12 or later, [uv](https://docs.astral.sh/uv/) and a TeX distribution with LuaLaTeX and latexmk (MiKTeX or TeX Live).

```sh
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
```
