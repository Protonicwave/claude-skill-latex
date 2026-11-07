# Poster

A conference or project poster, read standing up from about two metres, by people who give it a minute unless the headline holds them. Design effort is high.

## Setup

- `\documentclass{beamer}` with `\usepackage[size=a0, orientation=portrait, scale=1.4]{beamerposter}` and `\usetheme{LaboratoryPoster}`, built with LuaLaTeX. A local poster class would be a supplied class to the lint and suppress every house-style tell, so the poster stays on Beamer.
- One frame, `[t]`, holding three columns of blocks at `0.31\linewidth` each, read top to bottom and left to right.
- The headline carries the title and the record strip.
- Figures use the `poster` mplstyle overlay: one column wide, 242 × 110 mm, 28 pt type against the 35 pt body, lines and marks heavy enough to read at a distance.

## Conventions

- Block titles state their content plainly: Question, Model, Method, Results, Conclusion, References. The title of the poster states the finding.
- The main result appears once in display size in the conclusion block.
- Figures and tables use Beamer's `figure` and `table` environments, which do not float, with numbered captions referred to as `Figure~\ref{fig:a}`; the theme does not load cleveref.
- Body text at the theme's size; never shrink a block's text to fit. Cut words instead, which is `/writing`'s job.

## Checks for this profile

- Render the poster at low resolution to see it as a whole, then at full resolution to read it. `render.py --dpi 20` gives a page the size of a screen.
- The three columns end at similar heights, with no block cut off at the foot of the sheet.
- No line of text is longer than about a third of the sheet width.
- Figure type is close to body size.
