r"""Lint LaTeX source for typesetting defects and the habits of generated documents.

Usage:
    python lint.py MAIN.tex

MAIN.tex is read with every file it brings in through \input, \include or
\subfile, resolved from its own folder as TeX does. Packages and beamer themes
loaded from that folder are read too, but only for the fonts and page layout
they set; they are not linted. Comments and verbatim material are ignored: the verbatim,
Verbatim, lstlisting, minted, comment and filecontents environments, \verb,
\lstinline and \mintinline.

Defects are wrong in any document and make the exit code 1. Tells are habits
of unconsidered or generated LaTeX: each is changed, or kept for a stated
reason, and none affects the exit code. House-style tells concern choices a
supplied template makes for the author, so when the document class is not one
of LaTeX's standard, KOMA-Script, memoir or beamer classes they are counted as
suppressed instead of reported. Exit code 2 means MAIN.tex or a package it
loads from its folder could not be read.

Limits: rules read the source, not the typeset page, so macros are not
expanded and anything built by \newcommand is judged only where it is used
literally. A `$` left open runs to the end of its file, hiding the rest from
the prose rules; the build reports the error. Arguments are matched to
balanced braces up to MAX_ARGUMENT_CHARS. Files reached through \import or
TEXINPUTS are not followed, so floats referred to only from such files are
reported as unreferenced.
"""

from __future__ import annotations

import argparse
import bisect
import io
import re
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import assert_never

MAX_FILES = 200
MAX_FILE_BYTES = 5_000_000
MAX_ARGUMENT_CHARS = 20_000
MAX_SHOWN_PER_RULE = 20
EXCERPT_CONTEXT_CHARS = 30
MAX_EXCERPT_CHARS = 90
# Prose rules see maths as a run of letters, so a quote or digit beside an
# equation is judged as it would be beside a word.
MATHS_FILLER = "M"


class Severity(StrEnum):
    DEFECT = "defect"
    TELL = "tell"


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    severity: Severity
    message: str
    fix: str
    is_house_style: bool = False


@dataclass(frozen=True, slots=True)
class Finding:
    rule: Rule
    file: str
    line: int
    excerpt: str


DEFECT, TELL = Severity.DEFECT, Severity.TELL

OBSOLETE_COMMAND = Rule(
    "obsolete-command",
    DEFECT,
    "a LaTeX 2.09 or plain TeX construct that spaces or combines wrongly in LaTeX",
    "use the replacement shown",
)
OBSOLETE_PACKAGE = Rule(
    "obsolete-package",
    DEFECT,
    "a package superseded by one that does the job correctly",
    "load the replacement shown",
)
LEGACY_ENCODING = Rule(
    "legacy-encoding",
    DEFECT,
    "fontenc or inputenc loaded with fontspec: fontenc can switch text back to a Type 1 "
    "font, and inputenc does nothing under LuaLaTeX",
    "remove the line; fontspec handles encoding",
)
ITALIC_OPERATOR = Rule(
    "italic-operator",
    DEFECT,
    "a function name typed as letters in maths sets as a product of italic variables",
    r"use the operator command, such as \sin or \exp, or \operatorname{name}",
)
ITALIC_UNIT = Rule(
    "italic-unit",
    DEFECT,
    "a unit typed in maths sets as italic variables",
    r"use \qty{value}{unit} from siunitx",
)
ITALIC_SUBSCRIPT_LABEL = Rule(
    "italic-subscript-label",
    DEFECT,
    "a descriptive subscript such as max or eff is a label, set upright (ISO 80000-2), "
    "not a product of variables",
    r"use \mathrm, as in T_\mathrm{max}",
)
HYPHEN_RANGE = Rule(
    "hyphen-range",
    DEFECT,
    "a range of numbers joined by a hyphen",
    r"use an en dash, 3--5, or \numrange from siunitx",
)
LETTER_TIMES = Rule(
    "letter-times",
    DEFECT,
    "the letter x used as a multiplication sign",
    r"use $32 \times 32$",
)
STRAIGHT_QUOTE = Rule(
    "straight-quote",
    DEFECT,
    "a straight quotation mark at the start of a word sets as a closing quote",
    "open with ` or `` and close with ' or ''",
)
ELLIPSIS = Rule(
    "ellipsis",
    DEFECT,
    "three full stops are spaced as full stops, not as an ellipsis",
    r"use \dots, or \cdots between operators in maths",
)
BREAKABLE_REFERENCE = Rule(
    "breakable-reference",
    DEFECT,
    "an ordinary space before a number reference or citation lets the line break there",
    r"join it with a tie, as in Figure~\ref{fig:a} or shown~\cite{key}",
)
SPLIT_CITATION = Rule(
    "split-citation",
    DEFECT,
    "adjacent citation commands set as separate brackets, [1][2]",
    r"cite the keys together, \cite{a,b}",
)
BLANK_LINE_BEFORE_DISPLAY = Rule(
    "blank-line-before-display",
    DEFECT,
    "a blank line before a display ends the paragraph, leaving an empty line above the equation",
    "remove the blank line",
)
PARAGRAPH_ENDED_BY_LINE_BREAK = Rule(
    "paragraph-ended-by-line-break",
    DEFECT,
    r"\\ before a blank line breaks a line that is already ending, leaving an underfull one",
    r"remove the \\; the blank line ends the paragraph",
)
LABEL_BEFORE_CAPTION = Rule(
    "label-before-caption",
    DEFECT,
    r"a \label before the \caption in a float takes the number of the section, not the float",
    r"put \label after \caption",
)
FLOAT_WITHOUT_CAPTION = Rule(
    "float-without-caption",
    DEFECT,
    "a float without a caption has no number to refer to",
    r"add a \caption that says what the reader should see",
)
CENTRE_ENVIRONMENT_IN_FLOAT = Rule(
    "centre-environment-in-float",
    DEFECT,
    "the center environment adds list spacing above and below inside a float",
    r"use \centering",
)
UNREFERENCED_FLOAT = Rule(
    "unreferenced-float",
    DEFECT,
    "a figure or table the text never refers to",
    r"label it and refer to it with \cref where the text discusses it, or remove it",
)
LEFTOVER_PLACEHOLDER = Rule(
    "leftover-placeholder",
    DEFECT,
    "placeholder or to-do material left in the text",
    "write the content or remove the marker",
)
UNREAD_INPUT = Rule(
    "unread-input",
    DEFECT,
    r"a file brought in with \input or \include could not be read",
    "check the path, which TeX resolves from the main document's folder",
)
MANUAL_LAYOUT = Rule(
    "manual-layout",
    TELL,
    "spacing, indentation or a page break set by hand in the text",
    "fix the cause in the style, or keep it for a stated reason such as an appendix break",
)
SLOPPY = Rule(
    "sloppy",
    TELL,
    r"\sloppy loosens every line to hide a few overfull ones",
    r"fix the lines that overflow, or give the style an \emergencystretch",
)
FORCED_FLOAT_PLACEMENT = Rule(
    "forced-float-placement",
    TELL,
    "[h] or [H] pins a float where it is written, leaving gaps or pushing it to the end",
    "use [tbp] and place the float after the paragraph that refers to it",
)
RULED_TABLE = Rule(
    "ruled-table",
    TELL,
    r"vertical rules or \hline make a grid",
    r"use booktabs: \toprule, \midrule and \bottomrule, and no vertical rules",
    is_house_style=True,
)
FIXED_FIGURE_WIDTH = Rule(
    "fixed-figure-width",
    TELL,
    "a figure sized in absolute units or by scale does not follow the text width",
    r"size it as a fraction of \linewidth and draw the plot at that width",
)
RASTER_FIGURE = Rule(
    "raster-figure",
    TELL,
    "a bitmap figure: plots and diagrams lose sharpness and searchable text",
    "export plots as PDF; keep PNG or JPEG for photographs",
)
INLINE_FRACTION = Rule(
    "inline-fraction",
    TELL,
    "a stacked fraction in running text shrinks and pushes the lines around it apart",
    "write a/b inline, or move the expression to a display",
)
UNDERLINE = Rule(
    "underline",
    TELL,
    "underlining is the typewriter's substitute for emphasis",
    r"use \emph",
)
NAMED_COLOUR = Rule(
    "named-colour",
    TELL,
    "a stock colour name in the text, outside the style's palette",
    "use the style's accent, or no colour",
    is_house_style=True,
)
UNIT_BY_HAND = Rule(
    "unit-by-hand",
    TELL,
    "a number and unit typed by hand",
    r"use \qty{value}{unit} so spacing and upright units are consistent",
    is_house_style=True,
)
ITALIC_DIFFERENTIAL = Rule(
    "italic-differential",
    TELL,
    "the differential d is set italic; ISO 80000-2 sets it upright",
    r"use \mathrm{d}, through a macro in the style",
    is_house_style=True,
)
ITALIC_CONSTANT_E = Rule(
    "italic-constant-e",
    TELL,
    "e with an exponent is set italic; ISO 80000-2 sets the exponential constant upright",
    r"use \mathrm{e}, or \exp for long exponents; keep e italic for the elementary charge",
    is_house_style=True,
)
TABLE_CAPTION_BELOW = Rule(
    "table-caption-below",
    TELL,
    "a table caption set below the table, though a table is read from the top",
    r"put \caption above the tabular",
    is_house_style=True,
)
FLOAT_BEFORE_REFERENCE = Rule(
    "float-before-reference",
    TELL,
    "the float comes before the first text that refers to it, so it can appear above that text",
    "move the float after the paragraph that first refers to it",
)
DEFAULT_TYPEFACE = Rule(
    "default-typeface",
    TELL,
    "no typeface is chosen, so the document is set in LaTeX's default Computer Modern",
    "choose text and maths fonts that match, or load the house style",
    is_house_style=True,
)
DEFAULT_MARGINS = Rule(
    "default-margins",
    TELL,
    "the text block is the standard class default, a narrow column in wide margins",
    "set the text block with geometry, or load the house style",
    is_house_style=True,
)

STANDARD_CLASSES = frozenset({"article", "report", "book", "extarticle", "extreport", "extbook"})
# These classes compute their own text block, so they are not judged on margins.
OWN_LAYOUT_CLASSES = frozenset({"scrartcl", "scrreprt", "scrbook", "memoir", "beamer"})
KNOWN_CLASSES = STANDARD_CLASSES | OWN_LAYOUT_CLASSES

OBSOLETE_COMMANDS = {
    r"\bf": r"\textbf or \bfseries",
    r"\it": r"\emph, \textit or \itshape",
    r"\rm": r"\textrm or \rmfamily, or \mathrm in maths",
    r"\sf": r"\textsf or \sffamily",
    r"\tt": r"\texttt or \ttfamily",
    r"\sc": r"\textsc or \scshape",
    r"\sl": r"\textsl or \slshape",
    r"\over": r"\frac",
    r"\atop": r"\binom or \genfrac",
    r"\centerline": r"\centering",
    r"\documentstyle": r"\documentclass",
    r"\begin{eqnarray}": "align from amsmath",
    "$$": r"\[ ... \] or equation*",
}
OBSOLETE_PACKAGES = {
    "a4": "geometry",
    "a4wide": "geometry",
    "anysize": "geometry",
    "fullpage": "geometry",
    "times": "fontspec, or newtxtext and newtxmath",
    "mathptm": "fontspec, or newtxtext and newtxmath",
    "pslatex": "fontspec, or newtxtext and newtxmath",
    "palatino": "fontspec, or newpxtext and newpxmath",
    "mathpple": "fontspec, or newpxtext and newpxmath",
    "euler": "eulervm",
    "epsfig": "graphicx",
    "epsf": "graphicx",
    "psfig": "graphicx",
    "subfigure": "subcaption",
    "caption2": "caption",
    "fancyheadings": "fancyhdr",
    "scrpage2": "scrlayer-scrpage",
    "doublespace": "setspace",
    "t1enc": "fontenc",
    "isolatin": "inputenc",
    "umlaute": "inputenc",
    "glossary": "glossaries",
}

OPERATORS = (
    "arcsin|arccos|arctan|sinh|cosh|tanh|coth|sin|cos|tan|cot|sec|csc|exp|log|ln|lg"
    "|det|lim|max|min|sup|inf|arg|deg|dim|ker|gcd"
)
MULTI_LETTER_UNITS = (
    "mm|cm|km|nm|pm|um|kg|mg|ms|ns|ps|us|Hz|kHz|MHz|GHz|THz|eV|meV|keV|MeV|GeV|TeV|mol"
    "|Pa|kPa|MPa|GPa|kJ|MJ|kW|MW|mW|mA|kV|mV|mT|dB|rad|sr"
)
SUBSCRIPT_LABELS = (
    "max|min|eff|tot|ext|int|exp|obs|rms|avg|ref|crit|sat|kin|pot|out|init|fin|final"
    "|true|est|err|sys|stat|theo|sim|meas|opt|peak"
)
STOCK_COLOURS = "red|green|blue|cyan|magenta|yellow|orange|purple|violet|brown|lime|olive|pink|teal"
FONT_PACKAGES = (
    "newtxtext|newtxmath|newpxtext|newpxmath|mathpazo|mathptmx|tgpagella|tgtermes|tgschola"
    "|tgbonum|libertinus|libertine|stix|stix2|ebgaramond|erewhon|fourier|charter|XCharter"
    "|kpfonts|cochineal|baskervillef|sourceserifpro|plex-serif|utopia|helvet|eulervm"
)
VERBATIM_ENVIRONMENTS = (
    "verbatim|Verbatim|BVerbatim|LVerbatim|lstlisting|minted|comment|filecontents"
)
MATHS_ENVIRONMENTS = "equation|align|alignat|flalign|gather|multline|eqnarray|displaymath|math"
DISPLAY_ENVIRONMENTS = "equation|align|alignat|flalign|gather|multline|displaymath"

MASK_TRIGGER = re.compile(
    r"(?P<comment>%)"
    rf"|\\begin\{{(?P<environment>(?:{VERBATIM_ENVIRONMENTS})\*?)\}}"
    r"|\\(?:verb\*?|lstinline(?:\[[^\]\n]*\])?|mintinline\{[^}\n]*\})(?P<delimiter>[^\sA-Za-z])"
    r"|\\[\s\S]"
)
MATHS_OPENER = re.compile(
    rf"\\begin\{{(?P<environment>(?:{MATHS_ENVIRONMENTS})\*?)\}}"
    r"|\\\(|\\\[|\$\$|\$|\\[\s\S]"
)
MATHS_CLOSERS = {"\\(": r"\\\)", "\\[": r"\\\]", "$$": r"\$\$", "$": r"\$"}
INLINE_OPENERS = frozenset({"$", "\\("})
BRACE = re.compile(r"\\[\s\S]|[{}]")
TRAILING_COMMENT = re.compile(r"(?<!\\)%\s*$")
NOT_NEWLINE = re.compile(r"[^\n]")
# Arguments that hold keys, paths or settings rather than prose or maths.
PROSE_ARGUMENT = re.compile(
    r"(?<!\\)\\(?:label|[A-Za-z]*ref(?:range)?|[cC]ite[A-Za-z]*|input|include|subfile"
    r"|includegraphics|graphicspath|url|href|usepackage|RequirePackage|documentclass"
    r"|bibliography|bibliographystyle|addbibresource|begin|end|lstinputlisting|num|qty|SI|si"
    r"|unit|ang|numrange|qtyrange|SIrange|tablenum|definecolor|color|textcolor|colorbox"
    r"|hypersetup|setlength|setcounter|newcommand|renewcommand|providecommand|newenvironment"
    r"|renewenvironment|DeclareMathOperator|pagestyle|thispagestyle|captionsetup|sisetup"
    r"|geometry|setmainfont|setsansfont|setmonofont|setmathfont)\*?\s*(?:\[[^\]]*\]\s*)*\{"
)
OPTIONAL_ARGUMENT = re.compile(r"(?<!\\)\\[A-Za-z]+\*?\s*(\[[^\]]*\])")
# A TikZ \foreach list such as {0,...,7} is loop syntax, not prose.
FOREACH_LIST = re.compile(r"(?<!\\)\\foreach\b[^{}]*?\bin\s*\{")
# A command definition up to its body; an xparse command has an argument
# specification in braces between the name and the body.
DEFINITION = re.compile(
    r"(?<!\\)\\(?:(?:re|provide)?newcommand\*?"
    r"|(?P<xparse>(?:New|Renew|Provide|Declare)DocumentCommand)|[egx]?def(?=\s*\\))"
    r"\s*(?:\{\s*\\[A-Za-z@]+\s*\}|\\[A-Za-z@]+)"
)
BEFORE_DEFINITION_BODY = re.compile(r"(?:\s|\[[^\]]*\]|#\d)*\{")
# Arguments inside maths that hold upright text, keys or units.
MATHS_ARGUMENT = re.compile(
    r"(?<!\\)\\(?:text[A-Za-z]*|math(?:rm|it|sf|tt|bf|cal|bb|frak|scr|normal)|operatorname"
    r"|mbox|hbox|label|[A-Za-z]*ref|[cC]ite[A-Za-z]*|begin|end|num|qty|SI|si|unit|ang"
    r"|numrange|qtyrange|SIrange|tag|intertext|shortintertext)\*?\s*(?:\[[^\]]*\]\s*)*\{"
)

BEGIN_DOCUMENT = re.compile(r"\\begin\s*\{document\}")
DOCUMENT_CLASS = re.compile(r"(?<!\\)\\documentclass\s*(?:\[[^\]]*\])?\s*\{(?P<name>[^{}]+)\}")
INPUT = re.compile(r"(?<!\\)\\(?:input|include|subfile)\s*\{(?P<name>[^{}]+)\}")
PACKAGE = re.compile(
    r"(?<!\\)\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{(?P<names>[^{}]*)\}"
)
# Beamer reads a theme named X from beamer<kind>themeX.sty.
THEME = re.compile(
    r"(?<!\\)\\use(?P<kind>|color|font|inner|outer)theme\s*(?:\[[^\]]*\])?\s*\{(?P<name>[^{}]+)\}"
)
OBSOLETE_COMMAND_PATTERN = re.compile(
    r"(?<!\\)(?:\\(?:bf|it|rm|sf|tt|sc|sl|over|atop|centerline|documentstyle)(?![A-Za-z])"
    r"|\\begin\{eqnarray\*?\}|\$\$[^$]*\$\$)"
)
FLOAT = re.compile(
    r"\\begin\{(?P<environment>(?:figure|table)\*?|wrapfigure|wraptable|sideways(?:figure|table))\}"
    r"(?P<body>.*?)\\end\{(?P=environment)\}",
    re.DOTALL,
)
CAPTION = re.compile(r"(?<!\\)\\caption(?![A-Za-z])")
LABEL = re.compile(r"(?<!\\)\\label\s*\{(?P<key>[^{}]*)\}")
TABULAR = re.compile(r"\\begin\{(?:tabular[*xy]?|longtable|tblr)\}")
CENTER_ENVIRONMENT = re.compile(r"\\begin\{center\}")
REFERENCE = re.compile(
    r"(?<!\\)\\(?:[cC]ref|[cC]pageref|ref|eqref|pageref|autoref|vref|nameref|labelcref"
    r"|[cC]refrange|[cC]pagerefrange)\*?\s*\{(?P<keys>[^{}]*)\}(?:\s*\{(?P<range_end>[^{}]*)\})?"
)
FONT_SETUP = re.compile(
    r"\\set(?:main|sans|mono|math)font\b|\\familydefault\b"
    rf"|\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{{[^{{}}]*\b(?:{FONT_PACKAGES})\b"
)
MARGIN_SETUP = re.compile(
    r"\\(?:new)?geometry\s*\{|\\setlength\s*\{?\s*\\textwidth"
    r"|\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{[^{}]*"
    r"\b(?:geometry|typearea|fullpage|a4wide|vmargin|anysize)\b"
)


class View(StrEnum):
    SOURCE = "source"
    # The source with command definitions blanked, so a macro that marks a gap
    # is judged where it is used, not where it is defined.
    OUTSIDE_DEFINITIONS = "outside definitions"
    PROSE = "prose"
    MATHS = "maths"
    INLINE_MATHS = "inline maths"


@dataclass(frozen=True, slots=True)
class PatternCheck:
    """A rule found by one pattern in one view of the source.

    The finding's line is that of the group named `at` when the pattern has one.
    """

    rule: Rule
    view: View
    pattern: re.Pattern[str]
    is_body_only: bool = False


PATTERN_CHECKS = (
    PatternCheck(
        ITALIC_OPERATOR,
        View.MATHS,
        re.compile(rf"(?<![\\A-Za-z])(?<!_)(?<!_\{{)(?:{OPERATORS})(?![A-Za-z])"),
    ),
    PatternCheck(
        ITALIC_UNIT,
        View.MATHS,
        re.compile(rf"\d\s*(?:\\[,;:! ]\s*|~\s*)?(?:{MULTI_LETTER_UNITS})(?![A-Za-z])"),
    ),
    PatternCheck(
        ITALIC_SUBSCRIPT_LABEL,
        View.MATHS,
        re.compile(
            rf"_\s*(?:\{{\s*(?:{SUBSCRIPT_LABELS})\s*\}}|(?:{SUBSCRIPT_LABELS})(?![A-Za-z]))"
        ),
    ),
    PatternCheck(
        HYPHEN_RANGE,
        View.PROSE,
        re.compile(r"(?<![\w.-])\d+(?:\.\d+)?-\d+(?:\.\d+)?(?![\w-]|\.\d)"),
    ),
    PatternCheck(
        LETTER_TIMES,
        View.PROSE,
        re.compile(r"(?<![\w.])(?!0x[0-9A-Fa-f])\d+(?:\.\d+)?\s?x\s?\d+(?:\.\d+)?(?!\w|\.\d)"),
    ),
    PatternCheck(
        STRAIGHT_QUOTE, View.PROSE, re.compile(r"(?:^|(?<=[\s(\[{]))[\"'](?=\w)", re.MULTILINE)
    ),
    PatternCheck(ELLIPSIS, View.PROSE, re.compile(r"(?<!\.)\.\.\.(?!\.)")),
    PatternCheck(ELLIPSIS, View.MATHS, re.compile(r"(?<!\.)\.\.\.(?!\.)")),
    PatternCheck(
        BREAKABLE_REFERENCE,
        View.SOURCE,
        re.compile(
            r"(?<=[\w.,;:)\]}'$])(?:[ \t]+\n?|\n)[ \t]*"
            r"(?P<at>\\(?:ref|eqref|pageref|cite|citep)(?![A-Za-z]))"
        ),
    ),
    PatternCheck(
        SPLIT_CITATION,
        View.SOURCE,
        re.compile(
            r"\\citep?\*?(?:\[[^\]]*\])*\{[^{}]*\}[ \t]*\n?[ \t]*[,;]?[ \t]*~?"
            r"(?P<at>\\citep?)(?![A-Za-z])"
        ),
    ),
    PatternCheck(
        BLANK_LINE_BEFORE_DISPLAY,
        View.SOURCE,
        re.compile(rf"\n[ \t]*\n[ \t]*(?P<at>\\begin\{{(?:{DISPLAY_ENVIRONMENTS})\*?\}}|\\\[)"),
    ),
    PatternCheck(
        PARAGRAPH_ENDED_BY_LINE_BREAK,
        View.SOURCE,
        re.compile(r"(?<!\\)(?P<at>\\\\)\*?(?:\[[^\]]*\])?[ \t]*%?[ \t]*\n[ \t]*\n"),
    ),
    PatternCheck(
        LEFTOVER_PLACEHOLDER,
        View.OUTSIDE_DEFINITIONS,
        re.compile(
            r"(?<!\\)\\(?:todo|lipsum|blindtext|Blindtext|missingfigure)(?![A-Za-z])"
            r"|\b(?:TODO|FIXME|XXX|TBD)\b|\?\?\?|(?i:lorem ipsum)"
        ),
    ),
    PatternCheck(
        MANUAL_LAYOUT,
        View.SOURCE,
        re.compile(
            r"(?<!\\)\\(?:vspace|hspace|vskip|hskip|bigskip|medskip|smallskip|noindent|newpage"
            r"|clearpage|cleardoublepage|pagebreak|linebreak|newline)(?![A-Za-z])\*?"
            r"(?:\{[^{}]*\})?"
        ),
        is_body_only=True,
    ),
    PatternCheck(
        SLOPPY, View.SOURCE, re.compile(r"(?<!\\)\\(?:sloppy(?![A-Za-z])|begin\{sloppypar\})")
    ),
    PatternCheck(
        FORCED_FLOAT_PLACEMENT,
        View.SOURCE,
        re.compile(r"\\begin\{(?:figure|table)\*?\}\s*\[(?:H|!?h!?)\]"),
    ),
    PatternCheck(
        RULED_TABLE,
        View.SOURCE,
        re.compile(
            r"\\begin\{(?:tabular\*?|tabularx|longtable)\}(?:\[[^\]]*\])?(?:\{[^{}]*\})?"
            r"\{(?:[^{}|]|\{[^{}]*\})*\||(?<!\\)\\(?:hline|cline)(?![A-Za-z])"
        ),
        is_body_only=True,
    ),
    PatternCheck(
        FIXED_FIGURE_WIDTH,
        View.SOURCE,
        re.compile(
            r"\\includegraphics\s*\[[^\]]*?\b(?:(?:width|height)\s*=\s*[\d.]+\s*"
            r"(?:cm|mm|in|pt|bp|pc|em|ex)\b|scale\s*=)"
        ),
    ),
    PatternCheck(
        RASTER_FIGURE,
        View.SOURCE,
        re.compile(
            r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{[^{}]*\.(?i:png|jpe?g|gif|bmp|tiff?)\s*\}"
        ),
    ),
    PatternCheck(INLINE_FRACTION, View.INLINE_MATHS, re.compile(r"(?<!\\)\\d?frac(?![A-Za-z])")),
    PatternCheck(
        UNDERLINE,
        View.PROSE,
        re.compile(r"(?<!\\)\\(?:underline|uline)(?![A-Za-z])"),
        is_body_only=True,
    ),
    PatternCheck(
        NAMED_COLOUR,
        View.SOURCE,
        re.compile(rf"\\(?:textcolor|color|colorbox)\s*\{{(?:{STOCK_COLOURS})\}}"),
        is_body_only=True,
    ),
    PatternCheck(
        UNIT_BY_HAND,
        View.PROSE,
        re.compile(
            rf"(?<![\w.{{=-])\d+(?:\.\d+)?(?:[ ~]|\\[,;: ])?(?:{MULTI_LETTER_UNITS}|[KmsgJWVANT])"
            r"(?!\w)"
        ),
    ),
    PatternCheck(
        ITALIC_DIFFERENTIAL,
        View.MATHS,
        re.compile(r"(?:\\[,;:!]|\\frac\s*\{|\}\s*\{)\s*(?P<at>d)(?=\s*(?:[A-Za-z]|\\[A-Za-z]))"),
    ),
    PatternCheck(ITALIC_CONSTANT_E, View.MATHS, re.compile(r"(?<![\\A-Za-z_])e\s*\^")),
)


@dataclass(frozen=True, slots=True)
class Source:
    """One .tex file, with views in which everything but one kind of text is blanked.

    Every view has the length and line breaks of the file, so an offset in any
    view is an offset in the file.
    """

    name: str
    masked: str
    outside_definitions: str
    prose: str
    maths: str
    inline_maths: str
    body_start: int
    line_starts: tuple[int, ...]

    def view(self, which: View) -> str:
        match which:
            case View.SOURCE:
                return self.masked
            case View.OUTSIDE_DEFINITIONS:
                return self.outside_definitions
            case View.PROSE:
                return self.prose
            case View.MATHS:
                return self.maths
            case View.INLINE_MATHS:
                return self.inline_maths
            case _:
                assert_never(which)

    def line_of(self, offset: int) -> int:
        return bisect.bisect_right(self.line_starts, offset)

    def finding(self, rule: Rule, start: int, end: int, excerpt: str | None = None) -> Finding:
        return Finding(rule, self.name, self.line_of(start), excerpt or self._excerpt(start, end))

    def _excerpt(self, start: int, end: int) -> str:
        """The finding's context on its own line, without the `%` of a blanked comment."""
        line_start = self.masked.rfind("\n", 0, start) + 1
        line_end = _line_end(self.masked, start)
        window = self.masked[
            max(line_start, start - EXCERPT_CONTEXT_CHARS) : min(
                line_end, end + EXCERPT_CONTEXT_CHARS
            )
        ]
        words = " ".join(TRAILING_COMMENT.sub("", window).split())
        if len(words) <= MAX_EXCERPT_CHARS:
            return words
        return words[: MAX_EXCERPT_CHARS - 3] + "..."


@dataclass(frozen=True, slots=True)
class MathsSpan:
    start: int
    end: int
    is_inline: bool


def _fill(text: str, spans: Iterable[tuple[int, int]], filler: str = " ") -> str:
    """Replace every character in the spans except newlines, keeping the length."""
    pieces: list[str] = []
    position = 0
    for span_start, end in sorted(spans):
        start = max(span_start, position)
        if start >= end:
            continue
        pieces += [text[position:start], NOT_NEWLINE.sub(filler, text[start:end])]
        position = end
    pieces.append(text[position:])
    return "".join(pieces)


def _line_end(text: str, start: int) -> int:
    end = text.find("\n", start)
    return len(text) if end < 0 else end


def mask_source(text: str) -> str:
    """Blank comments and verbatim material, keeping each comment's `%`.

    The `%` stays because TeX drops the line break after it: a comment line is
    not a blank line, and a line ending in a comment does not end in a space.
    """
    spans: list[tuple[int, int]] = []
    position = 0
    while (trigger := MASK_TRIGGER.search(text, position)) is not None:
        end = _masked_end(text, trigger)
        if end > trigger.end():
            spans.append((trigger.end(), end))
        position = max(end, trigger.end())
    return _fill(text, spans)


def _masked_end(text: str, trigger: re.Match[str]) -> int:
    if trigger.group("comment"):
        return _line_end(text, trigger.end())
    if environment := trigger.group("environment"):
        closing = text.find(f"\\end{{{environment}}}", trigger.end())
        return len(text) if closing < 0 else closing
    if delimiter := trigger.group("delimiter"):
        line_end = _line_end(text, trigger.end())
        closing = text.find("}" if delimiter == "{" else delimiter, trigger.end(), line_end)
        return line_end if closing < 0 else closing
    return trigger.end()


def maths_spans(masked: str) -> list[MathsSpan]:
    spans: list[MathsSpan] = []
    position = 0
    while (opener := MATHS_OPENER.search(masked, position)) is not None:
        token = opener.group()
        if environment := opener.group("environment"):
            closer = re.escape(f"\\end{{{environment}}}")
        elif token in MATHS_CLOSERS:
            closer = MATHS_CLOSERS[token]
        else:
            position = opener.end()  # an escaped character, such as \$
            continue
        end = _closing_position(masked, opener.end(), closer)
        spans.append(MathsSpan(opener.start(), end, token in INLINE_OPENERS))
        position = end
    return spans


def _closing_position(text: str, start: int, closer: str) -> int:
    """Find the end of the closer, stepping over escaped characters; the text's end if none."""
    pattern = re.compile(rf"(?P<closer>{closer})|\\[\s\S]")
    position = start
    while (match := pattern.search(text, position)) is not None:
        if match.group("closer") is not None:
            return match.end()
        position = match.end()
    return len(text)


def _closing_brace(text: str, open_index: int) -> int | None:
    depth = 0
    limit = min(len(text), open_index + MAX_ARGUMENT_CHARS)
    for match in BRACE.finditer(text, open_index, limit):
        if match.group() == "{":
            depth += 1
        elif match.group() == "}":
            depth -= 1
            if depth == 0:
                return match.start()
    return None


def _argument_spans(text: str, command: re.Pattern[str]) -> list[tuple[int, int]]:
    """Spans inside the braced argument that each match of `command` opens."""
    spans = []
    for match in command.finditer(text):
        close = _closing_brace(text, match.end() - 1)
        if close is not None:
            spans.append((match.end(), close))
    return spans


def _definition_spans(text: str) -> list[tuple[int, int]]:
    """Spans of command definitions, from the defining command to the end of the body."""
    spans = []
    for match in DEFINITION.finditer(text):
        end = match.end()
        for _ in range(2 if match.group("xparse") else 1):
            opening = BEFORE_DEFINITION_BODY.match(text, end)
            close = None if opening is None else _closing_brace(text, opening.end() - 1)
            if close is None:
                break
            end = close + 1
        spans.append((match.start(), end))
    return spans


def _outside(spans: Sequence[MathsSpan], length: int) -> list[tuple[int, int]]:
    gaps = []
    position = 0
    for span in spans:
        gaps.append((position, span.start))
        position = span.end
    gaps.append((position, length))
    return gaps


def make_source(name: str, text: str, *, in_body: bool) -> Source:
    """Build the views of a file.

    `in_body` says whether the file was brought in after \\begin{document}. A
    file with its own \\begin{document} starts its body there instead, and a
    file with a \\documentclass but no \\begin{document} has no body.
    """
    masked = mask_source(text)
    spans = maths_spans(masked)
    prose = _fill(masked, ((span.start, span.end) for span in spans), MATHS_FILLER)
    prose = _fill(prose, _argument_spans(prose, PROSE_ARGUMENT))
    prose = _fill(prose, _argument_spans(prose, FOREACH_LIST))
    prose = _fill(prose, (match.span(1) for match in OPTIONAL_ARGUMENT.finditer(prose)))
    maths = _fill(masked, _outside(spans, len(masked)))
    maths = _fill(maths, _argument_spans(maths, MATHS_ARGUMENT))
    inline = [span for span in spans if span.is_inline]
    begin = BEGIN_DOCUMENT.search(masked)
    if begin is not None:
        body_start = begin.end()
    elif in_body and DOCUMENT_CLASS.search(masked) is None:
        body_start = 0
    else:
        body_start = len(masked)
    return Source(
        name=name,
        masked=masked,
        outside_definitions=_fill(masked, _definition_spans(masked)),
        prose=prose,
        maths=maths,
        inline_maths=_fill(maths, _outside(inline, len(maths))),
        body_start=body_start,
        line_starts=(0, *(match.end() for match in re.finditer("\n", masked))),
    )


class UnreadableError(Exception):
    """A source file is missing, too large or cannot be read."""


def _read_text(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
    except FileNotFoundError as error:
        raise UnreadableError("not found") from error
    except OSError as error:
        raise UnreadableError(f"could not be read: {error.strerror}") from error
    if len(data) > MAX_FILE_BYTES:
        raise UnreadableError(f"larger than {MAX_FILE_BYTES} bytes")
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


@dataclass(frozen=True, slots=True)
class Segment:
    """A stretch of one file read without interruption by an \\input."""

    source: Source
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Document:
    sources: tuple[Source, ...]
    segments: tuple[Segment, ...]
    package_sources: tuple[str, ...]
    unread: tuple[Finding, ...]


def read_document(main: Path) -> Document:
    """Read the main file and its inputs in the order TeX reads them.

    Raises UnreadableError when the main file or a local package cannot be read;
    an input that cannot be read becomes an unread-input finding.
    """
    folder = main.parent
    root = make_source(main.name, _read_text(main), in_body=True)
    sources, segments, unread = [root], [], []
    seen = {main.resolve()}
    stack = [(root, 0)]
    while stack:
        source, position = stack.pop()
        directive = INPUT.search(source.masked, position)
        if directive is None:
            segments.append(Segment(source, position, len(source.masked)))
            continue
        segments.append(Segment(source, position, directive.start()))
        stack.append((source, directive.end()))
        child = _read_input(folder, source, directive, seen)
        if isinstance(child, Finding):
            unread.append(child)
        elif child is not None:
            sources.append(child)
            stack.append((child, 0))
    packages = _local_packages(folder, sources)
    return Document(tuple(sources), tuple(segments), packages, tuple(unread))


def _read_input(
    folder: Path, parent: Source, directive: re.Match[str], seen: set[Path]
) -> Source | Finding | None:
    """Read the file an \\input names, or explain why not; None if it was read already."""
    name = directive.group("name").strip().strip('"')
    path = _input_path(folder, name)
    if path.resolve() in seen:
        return None
    if len(seen) >= MAX_FILES:
        reason = f"not read, the document has more than {MAX_FILES} files"
        return parent.finding(UNREAD_INPUT, directive.start(), directive.end(), f"{name}: {reason}")
    try:
        text = _read_text(path)
    except UnreadableError as error:
        return parent.finding(UNREAD_INPUT, directive.start(), directive.end(), f"{name}: {error}")
    seen.add(path.resolve())
    in_body = directive.start() >= parent.body_start
    return make_source(_display_name(path, folder), text, in_body=in_body)


def _input_path(folder: Path, name: str) -> Path:
    """Resolve an input as TeX does: NAME.tex first, then NAME as written."""
    if name.endswith(".tex"):
        return folder / name
    candidates = (folder / f"{name}.tex", folder / name)
    return next((path for path in candidates if path.is_file()), candidates[0])


def _display_name(path: Path, folder: Path) -> str:
    try:
        return path.relative_to(folder, walk_up=True).as_posix()
    except ValueError:  # on another drive, so no relative path exists
        return path.as_posix()


def _package_names(masked: str) -> list[str]:
    return [
        name.strip()
        for match in PACKAGE.finditer(masked)
        for name in match.group("names").split(",")
        if name.strip()
    ]


def _theme_names(masked: str) -> list[str]:
    return [
        f"beamer{match.group('kind')}theme{match.group('name').strip()}"
        for match in THEME.finditer(masked)
    ]


def _local_packages(folder: Path, sources: Sequence[Source]) -> tuple[str, ...]:
    """Masked text of every package and beamer theme loaded from the document's own folder."""
    pending = [
        name
        for source in sources
        for name in _package_names(source.masked) + _theme_names(source.masked)
    ]
    seen: set[str] = set()
    texts: list[str] = []
    while pending and len(texts) < MAX_FILES:
        name = pending.pop()
        path = folder / f"{name}.sty"
        if name in seen or not path.is_file():
            continue
        seen.add(name)
        try:
            masked = mask_source(_read_text(path))
        except UnreadableError as error:
            raise UnreadableError(f"package {path.name}: {error}") from error
        texts.append(masked)
        pending += _package_names(masked) + _theme_names(masked)
    return tuple(texts)


def check_patterns(source: Source) -> list[Finding]:
    findings = []
    for check in PATTERN_CHECKS:
        start = source.body_start if check.is_body_only else 0
        located = "at" in check.pattern.groupindex
        for match in check.pattern.finditer(source.view(check.view), start):
            offset = match.start("at") if located else match.start()
            findings.append(source.finding(check.rule, offset, match.end()))
    return findings


def check_obsolete_commands(source: Source) -> list[Finding]:
    findings = []
    for match in OBSOLETE_COMMAND_PATTERN.finditer(source.masked):
        command = "$$" if match.group().startswith("$$") else match.group().replace("*", "")
        replacement = f"{command}: use {OBSOLETE_COMMANDS[command]}"
        findings.append(source.finding(OBSOLETE_COMMAND, match.start(), match.end(), replacement))
    return findings


def check_packages(source: Source, has_fontspec: bool) -> list[Finding]:
    findings = []
    for match in PACKAGE.finditer(source.masked):
        for name in (part.strip() for part in match.group("names").split(",")):
            if name in OBSOLETE_PACKAGES:
                replacement = f"{name}: use {OBSOLETE_PACKAGES[name]}"
                findings.append(
                    source.finding(OBSOLETE_PACKAGE, match.start(), match.end(), replacement)
                )
            elif has_fontspec and name in ("fontenc", "inputenc"):
                findings.append(source.finding(LEGACY_ENCODING, match.start(), match.end()))
    return findings


def check_floats(source: Source) -> list[Finding]:
    findings = []
    for match in FLOAT.finditer(source.masked):
        body, offset = match.group("body"), match.start("body")
        findings += [
            source.finding(
                CENTRE_ENVIRONMENT_IN_FLOAT, offset + found.start(), offset + found.end()
            )
            for found in CENTER_ENVIRONMENT.finditer(body)
        ]
        caption = CAPTION.search(body)
        if caption is None:
            findings.append(source.finding(FLOAT_WITHOUT_CAPTION, match.start(), match.start()))
            continue
        label = LABEL.search(body)
        if label is not None and label.start() < caption.start():
            findings.append(
                source.finding(LABEL_BEFORE_CAPTION, offset + label.start(), offset + label.end())
            )
        tabular = TABULAR.search(body)
        is_table = "table" in match.group("environment")
        if is_table and tabular is not None and tabular.start() < caption.start():
            findings.append(
                source.finding(
                    TABLE_CAPTION_BELOW, offset + caption.start(), offset + caption.end()
                )
            )
    return findings


Position = tuple[int, int]


def _first_references(document: Document) -> dict[str, Position]:
    """The reading position, as (segment, offset), of each label's first reference."""
    first: dict[str, Position] = {}
    for order, segment in enumerate(document.segments):
        masked = segment.source.masked
        for match in REFERENCE.finditer(masked, segment.start, segment.end):
            keys = f"{match.group('keys')},{match.group('range_end') or ''}".split(",")
            for key in (key.strip() for key in keys if key.strip()):
                first.setdefault(key, (order, match.start()))
    return first


def _placed_floats(document: Document) -> list[tuple[Position, Source, re.Match[str]]]:
    floats = {source.name: list(FLOAT.finditer(source.masked)) for source in document.sources}
    placed = []
    for order, segment in enumerate(document.segments):
        for match in floats[segment.source.name]:
            if segment.start <= match.start() < segment.end:
                placed.append(((order, match.start()), segment.source, match))
    return placed


def check_references(document: Document) -> list[Finding]:
    first_references = _first_references(document)
    findings = []
    for position, source, match in _placed_floats(document):
        labels = [label.group("key").strip() for label in LABEL.finditer(match.group("body"))]
        mentions = [first_references[label] for label in labels if label in first_references]
        if not mentions:
            findings.append(source.finding(UNREFERENCED_FLOAT, match.start(), match.start()))
        elif min(mentions) > position:
            findings.append(source.finding(FLOAT_BEFORE_REFERENCE, match.start(), match.start()))
    return findings


def check_defaults(document: Document, document_class: re.Match[str]) -> list[Finding]:
    """House-style tells about what the document leaves at LaTeX's defaults."""
    root = document.sources[0]
    settings = "\n".join(
        [*(source.masked for source in document.sources), *document.package_sources]
    )
    start, end = document_class.span()
    findings = []
    if FONT_SETUP.search(settings) is None:
        findings.append(root.finding(DEFAULT_TYPEFACE, start, end))
    is_own_layout = document_class.group("name").strip() in OWN_LAYOUT_CLASSES
    if not is_own_layout and MARGIN_SETUP.search(settings) is None:
        findings.append(root.finding(DEFAULT_MARGINS, start, end))
    return findings


@dataclass(frozen=True, slots=True)
class LintResult:
    findings: tuple[Finding, ...]
    suppressed: tuple[Finding, ...]
    document_class: str | None
    files_read: int


def lint(main: Path) -> LintResult:
    """Lint a document and its inputs. Raises UnreadableError as read_document does."""
    document = read_document(main)
    root = document.sources[0]
    loaded = {
        name
        for masked in (*(source.masked for source in document.sources), *document.package_sources)
        for name in _package_names(masked)
    }
    has_fontspec = bool(loaded & {"fontspec", "unicode-math"})
    findings = list(document.unread)
    for source in document.sources:
        findings += check_patterns(source)
        findings += check_obsolete_commands(source)
        findings += check_packages(source, has_fontspec)
        findings += check_floats(source)
    class_match = DOCUMENT_CLASS.search(root.masked)
    document_class = class_match.group("name").strip() if class_match else None
    if class_match is not None:
        findings += check_references(document)
        findings += check_defaults(document, class_match)
    order = {source.name: index for index, source in enumerate(document.sources)}
    findings.sort(key=lambda finding: (order[finding.file], finding.line))
    is_supplied = document_class is not None and document_class not in KNOWN_CLASSES
    return LintResult(
        findings=tuple(f for f in findings if not (is_supplied and f.rule.is_house_style)),
        suppressed=tuple(f for f in findings if is_supplied and f.rule.is_house_style),
        document_class=document_class,
        files_read=len(document.sources),
    )


def _counted(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def format_report(document_name: str, result: LintResult) -> str:
    defects = [finding for finding in result.findings if finding.rule.severity is DEFECT]
    tells = [finding for finding in result.findings if finding.rule.severity is TELL]
    lines = [
        f"{document_name}: {_counted(len(defects), 'defect')}, {_counted(len(tells), 'tell')}"
        f" in {_counted(result.files_read, 'file')}"
    ]
    if result.suppressed:
        lines.append(
            f"{_counted(len(result.suppressed), 'house-style tell')} suppressed: "
            f"class {result.document_class} sets the style"
        )
    for heading, group in (("Defects", defects), ("Tells", tells)):
        if group:
            lines += ["", heading, *_format_group(group)]
    rules = dict.fromkeys(finding.rule for finding in (*defects, *tells))
    if rules:
        lines += ["", "Rules"]
        lines += [
            f"  {rule.rule_id} ({rule.severity}): {rule.message}. Fix: {rule.fix}."
            for rule in rules
        ]
    return "\n".join(lines)


def _format_group(group: list[Finding]) -> list[str]:
    lines = []
    shown: Counter[str] = Counter()
    for finding in group:
        shown[finding.rule.rule_id] += 1
        if shown[finding.rule.rule_id] <= MAX_SHOWN_PER_RULE:
            location = f"{finding.file}:{finding.line}"
            lines.append(f"  {location}  {finding.rule.rule_id}  {finding.excerpt}")
    lines += [
        f"  {rule_id}: {total - MAX_SHOWN_PER_RULE} more not shown"
        for rule_id, total in shown.items()
        if total > MAX_SHOWN_PER_RULE
    ]
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("document", type=Path, help="the main .tex file")
    args = parser.parse_args(argv)

    document = args.document.resolve()
    if document.suffix != ".tex" or not document.is_file():
        print(f"expected an existing .tex file, got {args.document}", file=sys.stderr)
        return 2
    try:
        result = lint(document)
    except UnreadableError as error:
        print(f"could not read {args.document}: {error}", file=sys.stderr)
        return 2

    if isinstance(sys.stdout, io.TextIOWrapper):
        # Excerpts quote characters a Windows console code page cannot encode.
        sys.stdout.reconfigure(errors="replace")
    print(format_report(document.name, result))
    return 1 if any(finding.rule.severity is DEFECT for finding in result.findings) else 0


if __name__ == "__main__":
    sys.exit(main())
