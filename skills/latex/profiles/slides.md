# Slides

A talk, viva or group-meeting presentation. The audience reads each slide in the seconds while they also listen, from the back of a room. Design effort is high: every frame is composed by eye.

## Setup

- `\documentclass[aspectratio=169]{beamer}` with `\usetheme{Laboratory}`, built with LuaLaTeX.
- The theme keeps the document faces: Erewhon text and maths, Source Sans for frame titles, block titles and the footline. A sans slide face would need a matching sans maths face, and the house sans has none.
- No navigation symbols. The footline carries the short title and the frame number over the total.
- Figures use the `slides` mplstyle overlay: 140 × 50 mm at 10 pt, heavier lines for a projector.

## Conventions

- **A frame title is the claim the frame supports**, as a sentence: "The small-angle model fits every length to within the timing error", not "Results".
- One idea per frame, with the evidence for it: a figure, a table or one equation. Words support the evidence; about 40 at most.
- Bullets only for parallel items, one level, each under a line.
- Tables and figures are not floats on a slide: no caption number, no label, no reference. A figure's caption is a line of text under it.
- Maths in a frame title takes `\texorpdfstring` for the bookmark.
- Citations as on a page, `~\cite{key}`, with a references frame at the end.
- Overlays (`\pause`, `\only`) only where the order of revealing carries the argument, such as a derivation built up step by step.

## Checks for this profile

- Render every frame. Nothing runs below the footline's hairline; no frame title wraps to a third line.
- Figure type is close to the slide text size, not much smaller.
- The frame count suits the talk length; about one frame per minute is a common budget, so check the user's time slot.
- The title frame carries the record strip with author, date and source.
