# Plan

A project plan or proposal: what the project will find out, how, and by when. Its readers are a supervisor who agrees it and a marker who later holds the final report against it, so each hypothesis states the result that would refute it and each risk states the check that shows it has come true.

## Setup

- `article` class at 11 pt with `\usepackage{laboratory}`, built with LuaLaTeX.
- The title is the question the project answers. `\kicker` names the kind of document or the module, and `\supervisor` puts the supervisor in the record strip.
- `\definebadge` in the preamble gives each hypothesis a series colour once, `seriesA` to `seriesD`. The badges in the text and the risk table, the work package bars in the Gantt chart and the marks in the figures then share one key.
- The Gantt chart is `figures/gantt.pdf`, drawn by `figures/gantt.py` from the tables at its top: tasks with their start and end weeks and how far each is done, milestones, risk triggers, breaks such as vacations, and the status week. Every time counts weeks from the start of the project, so week 1 runs from 0 to 1, a task from 0 to 3 fills weeks 1 to 3, and a milestone at 3 falls at the end of week 3. Edit the tables and run `python figures/gantt.py`, which needs matplotlib and LuaLaTeX. It stops before drawing, naming the entry, on a repeated task or mark code, a task or break that does not end after it starts or that runs outside the chart's weeks, progress given to a work package or past the status week, and a milestone or trigger outside the chart or on a task that is not in the table.
- Under a module's plan template or form, keep the template and take only the conventions below.

## Sections and what each holds

| Part | Holds |
|---|---|
| Title and record strip | The question, author, supervisor, date, and `\source` pointing at the pilot's analysis |
| Aim | A `statement` block: one or two sentences on what will be measured or built, and to what precision |
| The question | What is known, with citations, and why it is worth a project; a `\paragraph` run-in head for a point that needs its own name |
| Hypotheses | A `claims` list, each item `\item[\badgetarget{H1}] \lead{The claim.}` followed by the result that would refute it, fixed before the run that tests it |
| Preliminary results | What the pilot shows, with its figure, and what it leaves open |
| Method | How each hypothesis will be tested, one `\paragraph` each, with the uncertainty each step carries |
| Work plan | The Gantt chart and a `milestones` list giving each milestone its week |
| Risks | A `tabularx` table at `\linewidth`: code, risk, the hypotheses it threatens as badges, likelihood and impact as `\level` chips, a trigger with its week, and a fallback, with `\band` on alternate rows |
| References | `\bibliography{refs}` with `apsrev4-2` |

## Checks for this profile

- Every `\badge` has a `\badgetarget`; `build.py` lists one without as a warning naming `badge.H1`.
- The chart, the milestones list and the risk table give each milestone and trigger the same week. Nothing checks this mechanically, so read them side by side after each change to `gantt.py`, and look at the chart itself: a milestone label near the end of the chart turns back to the left of its mark, where it can meet a risk label on the same row.
- Every hypothesis has a refutation and every risk a trigger with its week; one without is unfinished.
- Three floats in a short plan are sensitive to the order of the sections. The skeleton's order puts each float after the text that cites it; after editing, look at every page for a float that has dropped below the next section's heading or the references. The cure is more text in the float's own section, or the section moved earlier, never `[h]`.
- Page count against any limit, counting only the pages the rule counts.
