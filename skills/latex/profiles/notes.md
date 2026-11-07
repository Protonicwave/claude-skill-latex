# Notes

Lecture, revision or derivation notes: read in pieces, returned to, searched. The reader needs to find a definition fast and follow a derivation without skipping steps.

## Setup

- `article` class at 11 pt with `\usepackage{laboratory}`, built with LuaLaTeX.
- A contents page after the title.
- Long notes split into one file per topic, brought in with `\input`.

## Conventions

- Open each section with what it establishes, then define, derive and apply.
- `definition` environments for terms a later section relies on, labelled `def:` and referred to with `\cref`.
- Derivations in `align`, one step per line, with the reason for a non-obvious step in words after the display, not squeezed beside it with `\quad\text{...}`.
- Number only the equations later sections use.
- `example` environments for worked examples, with the numbers through siunitx.
- Code in `lstlisting` with a caption and label when the text refers to it.
- A summary box or bold "key result" is a tell; a numbered, labelled equation is how notes mark what matters.

## Checks for this profile

- Every `definition` and every numbered equation is referred to at least once, or loses its label and number.
- A derivation does not break across a page between a step and its justification; if it does, look for a float pushing it.
- The contents page shows section titles that say what each section establishes.
