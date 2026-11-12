"""Build a LaTeX document with latexmk and report what its log says is wrong.

Usage:
    python build.py MAIN.tex [--engine lualatex|pdflatex] [--outdir DIR]
                             [--timeout-seconds N]

latexmk runs in the document's folder with nonstop interaction, halting on the
first error, and writes into DIR (default `build`, relative to the document).
Every rule runs at least once (latexmk -g), so the log always comes from this
build; a log, BibTeX log or PDF this run did not write is ignored as left over.
The document's .aux, .log and latexmk's records of earlier runs are deleted
first, so a run that stopped before the bibliography cannot leave BibTeX an
.aux with no database in it: TeX always runs before BibTeX.
Without --engine, a latexmkrc or .latexmkrc in the document's folder chooses
the engine, as it does for an editor; with neither, LuaLaTeX is used.
The TeX log and any BibTeX log are then read into findings. Defects need
fixing before the document is handed back: errors, overfull boxes wider than
OVERFULL_TOLERANCE_PT, underfull boxes at or above UNDERFULL_BADNESS_LIMIT,
undefined references and citations, multiply defined labels, missing glyphs,
font substitutions and BibTeX errors. Everything else is a warning to judge.

Exit code 0 means no defects, 1 means defects or a failed build, 2 means a
bad argument or latexmk not found.

Limits: the log is read line by line after rejoining lines TeX wrapped at its
print width, so a genuine line of 79 bytes or more is joined to the next
unless the next starts a message. The file
a finding belongs to comes from the parentheses TeX writes as it opens and
closes files; unbalanced parentheses in a package's own log output can shift
it. Biber's log is not read, but citations it fails to resolve still show as
undefined in the TeX log. Only the first MAX_LOG_BYTES of a log are read. A
project latexmkrc that sets $aux_dir or $jobname moves or renames the log,
which is then reported as missing.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import signal
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

DEFAULT_TIMEOUT_SECONDS = 600
KILL_TIMEOUT_SECONDS = 30
MAX_PRINT_LINE_BYTES = 79
MAX_LOG_BYTES = 50_000_000
MAX_CONTINUATION_LINES = 20
MAX_CONTEXT_LINES = 20
MAX_SHOWN_PER_KIND = 20
FAILURE_TAIL_LINES = 15
OVERFULL_TOLERANCE_PT = 1.0
UNDERFULL_BADNESS_LIMIT = 10_000

CREATE_SUSPENDED = 0x0000_0004
PROCESS_TERMINATE = 0x0001
PROCESS_SET_QUOTA = 0x0100
PROCESS_SUSPEND_RESUME = 0x0800


class Engine(StrEnum):
    LUALATEX = "lualatex"
    PDFLATEX = "pdflatex"


ENGINE_FLAGS = {Engine.LUALATEX: "-lualatex", Engine.PDFLATEX: "-pdf"}
DEFAULT_ENGINE = Engine.LUALATEX
LATEXMKRC_NAMES = ("latexmkrc", ".latexmkrc")
# The files a build writes, read only when this run wrote them.
OUTPUTS = (".log", ".blg", ".pdf")
# What latexmk carries from one run into the next, cleared before each build.
# Once any of these records that the document uses BibTeX, latexmk -g runs
# BibTeX before TeX. A run that stopped before \bibliography leaves an .aux
# naming no database, so BibTeX fails and latexmk stops without running TeX.
# Clearing these files, unlike latexmk -gg, keeps the PDF, so a failing build
# still leaves something to look at.
CARRIED_STATE = (".aux", ".fdb_latexmk", ".fls", ".log")


class Severity(StrEnum):
    DEFECT = "defect"
    WARNING = "warning"


class Kind(StrEnum):
    ERROR = "error"
    OVERFULL_BOX = "overfull box"
    UNDERFULL_BOX = "underfull box"
    UNDEFINED_REFERENCE = "undefined reference"
    UNDEFINED_CITATION = "undefined citation"
    MULTIPLY_DEFINED_LABEL = "multiply defined label"
    MISSING_GLYPH = "missing glyph"
    FONT_SUBSTITUTION = "font substitution"
    BIBLIOGRAPHY = "bibliography"
    BUILD = "build"
    WARNING = "warning"


STOPPING_KINDS = frozenset({Kind.ERROR, Kind.BUILD})


@dataclass(frozen=True, slots=True)
class Finding:
    kind: Kind
    severity: Severity
    message: str
    file: str | None = None
    line: int | None = None


MESSAGE_START = re.compile(
    rb"^(! |Overfull \\|Underfull \\|Missing character: "
    rb"|(LaTeX|LaTeX Font|Package \S+|Class \S+|Module \S+) Warning: "
    rb"|\S.*?\.[A-Za-z]+:\d+: )"
)
BOX = re.compile(
    r"^(?P<which>Overfull|Underfull) \\[hv]box "
    r"\((?:(?P<points>[\d.]+)pt too (?:wide|high)|badness (?P<badness>\d+))\)"
)
BOX_LINE = re.compile(r"at lines? (\d+)")
BANG_ERROR = re.compile(r"^! (?P<message>.+)$")
FILE_LINE_ERROR = re.compile(r"^(?P<file>\S.*?\.[A-Za-z]+):(?P<line>\d+): (?P<message>.+)$")
ERROR_CONSEQUENCE = re.compile(r"Emergency stop|==> Fatal error occurred")
CONTEXT_LINE = re.compile(r"^l\.(\d+)")
WARNING = re.compile(
    r"^(?P<source>LaTeX|LaTeX Font|Package \S+|Class \S+|Module \S+) Warning: (?P<message>.*)$"
)
CONTINUATION = re.compile(r"^\([A-Za-z][\w@-]*\)\s+(?P<text>.*)$")
INPUT_LINE = re.compile(r"on input line (\d+)")
MISSING_GLYPH = re.compile(r"^Missing character: There is no .+ in font .+!$")
# The PDF writer's warnings, such as a link to a destination never set. pdfTeX
# writes them straight after page numbers, mid-line; LuaTeX's backend writes
# them on a line of their own at the end of the run. Neither names a source.
PDF_WRITER_WARNING = re.compile(r"(?:pdfTeX warning(?: \([^)]*\))?|warning  \(pdf backend\)): .+$")
PARENTHESIS = re.compile(r"[()]")
OPENED_FILE = re.compile(
    r'"(?P<quoted>[^"]+)"|(?P<bare>[^()"\s][^()"]*?\.[A-Za-z][A-Za-z0-9]*)(?=[\s()]|$)'
)
BIBTEX_ERROR_LOCATION = re.compile(r"^(?P<before>.*?)---line (?P<line>\d+) of file (?P<file>.+)$")
BIBTEX_ERROR_WHILE = re.compile(r"^(?P<message>.+?)---while reading file (?P<file>.+)$")

WARNING_KINDS = (
    (re.compile(r"^Reference [`'].+?' on page .+ undefined"), Kind.UNDEFINED_REFERENCE),
    (re.compile(r"^Citation [`'].+?' .*undefined"), Kind.UNDEFINED_CITATION),
    (re.compile(r"^Label [`'].+?' multiply defined"), Kind.MULTIPLY_DEFINED_LABEL),
    (re.compile(r"^Font shape [`']"), Kind.FONT_SUBSTITUTION),
)
# End-of-run summaries repeat what the individual warnings already reported.
WARNING_SUMMARY = re.compile(
    r"^(There were undefined (references|citations)"
    r"|There were multiply-defined labels"
    r"|Some font shapes were not available)"
)


def unwrap(log: bytes) -> list[str]:
    """Rejoin lines TeX broke at its print width and decode them.

    Width is measured in bytes before decoding, because TeX counts bytes and a
    multibyte character would otherwise make a wrapped line look short. TeX
    wraps at 79 bytes, but LuaTeX and its Lua modules sometimes wrap at 80, so
    any line that long is a fragment unless the next line starts a message:
    TeX begins a message on a fresh line straight after a full one.
    """
    lines: list[str] = []
    pending = b""
    raw_lines = log.splitlines()
    for index, raw in enumerate(raw_lines):
        pending += raw
        following = raw_lines[index + 1] if index + 1 < len(raw_lines) else b""
        is_fragment = len(raw) >= MAX_PRINT_LINE_BYTES and not MESSAGE_START.match(following)
        if not is_fragment:
            lines.append(pending.decode("utf-8", errors="replace"))
            pending = b""
    if pending:
        lines.append(pending.decode("utf-8", errors="replace"))
    return lines


def parse_log(log: bytes) -> list[Finding]:
    """Read a TeX log into findings, in the order they occur."""
    lines = unwrap(log)
    findings: list[Finding] = []
    open_files: list[str | None] = []
    index = 0
    while index < len(lines):
        entry = _parse_entry(lines, index, _current_file(open_files))
        if entry is None:
            findings.extend(_read_plain_line(lines[index], open_files))
            index += 1
            continue
        found, next_index = entry
        # An entry that consumed nothing would loop forever.
        assert next_index > index  # noqa: S101 (an invariant, not input validation)
        findings.extend(found)
        index = next_index
    return findings


def _current_file(open_files: list[str | None]) -> str | None:
    return next((name for name in reversed(open_files) if name), None)


def _read_plain_line(line: str, open_files: list[str | None]) -> list[Finding]:
    """Track the files a line opens and closes, and report a PDF writer warning in it."""
    warning = PDF_WRITER_WARNING.search(line)
    if warning is None:
        _track_files(line, open_files)
        return []
    _track_files(line[: warning.start()], open_files)
    here = _current_file(open_files)
    # The warning's own parentheses balance; any after them close files.
    _track_files(line[warning.start() :], open_files)
    return [Finding(Kind.WARNING, Severity.WARNING, warning.group(), here)]


def _parse_entry(
    lines: list[str], index: int, current_file: str | None
) -> tuple[list[Finding], int] | None:
    for parse in (_parse_box, _parse_error, _parse_warning, _parse_missing_glyph):
        entry = parse(lines, index, current_file)
        if entry is not None:
            return entry
    return None


def _track_files(line: str, open_files: list[str | None]) -> None:
    for mark in PARENTHESIS.finditer(line):
        if mark.group() == "(":
            opened = OPENED_FILE.match(line, mark.end())
            open_files.append(_display_path(opened) if opened else None)
        elif open_files:
            open_files.pop()


def _display_path(opened: re.Match[str]) -> str:
    path = opened.group("quoted") or opened.group("bare")
    return path.removeprefix("./")


def _parse_box(
    lines: list[str], index: int, current_file: str | None
) -> tuple[list[Finding], int] | None:
    match = BOX.match(lines[index])
    if match is None:
        return None
    if match.group("which") == "Overfull":
        kind = Kind.OVERFULL_BOX
        is_defect = float(match.group("points") or 0) > OVERFULL_TOLERANCE_PT
    else:
        kind = Kind.UNDERFULL_BOX
        is_defect = int(match.group("badness") or 0) >= UNDERFULL_BADNESS_LIMIT
    at_line = BOX_LINE.search(lines[index])
    finding = Finding(
        kind=kind,
        severity=Severity.DEFECT if is_defect else Severity.WARNING,
        message=lines[index],
        file=current_file,
        line=int(at_line.group(1)) if at_line else None,
    )
    # The typeset material that follows can hold unbalanced parentheses, so
    # it is skipped rather than fed to the file tracker.
    return [finding], _after_blank_line(lines, index + 1)


def _after_blank_line(lines: list[str], start: int) -> int:
    end = min(len(lines), start + MAX_CONTEXT_LINES)
    for index in range(start, end):
        if not lines[index].strip():
            return index + 1
    return start


def _parse_error(
    lines: list[str], index: int, current_file: str | None
) -> tuple[list[Finding], int] | None:
    file, line = current_file, None
    located = FILE_LINE_ERROR.match(lines[index])
    if located is not None:
        file = located.group("file").removeprefix("./")
        line = int(located.group("line"))
        message = located.group("message")
    else:
        bang = BANG_ERROR.match(lines[index])
        if bang is None:
            return None
        message = bang.group("message")
    message, next_index = _gather_continuation(lines, index + 1, message)
    next_index, context_line = _skip_error_context(lines, next_index)
    if ERROR_CONSEQUENCE.search(message):
        return [], next_index
    finding = Finding(Kind.ERROR, Severity.DEFECT, message, file, line or context_line)
    return [finding], next_index


def _skip_error_context(lines: list[str], start: int) -> tuple[int, int | None]:
    """Find the `l.<n>` line TeX prints after an error and step past its context."""
    end = min(len(lines), start + MAX_CONTEXT_LINES)
    for index in range(start, end):
        context = CONTEXT_LINE.match(lines[index])
        if context is not None:
            return min(len(lines), index + 2), int(context.group(1))
    return start, None


def _gather_continuation(lines: list[str], start: int, message: str) -> tuple[str, int]:
    parts = [message.strip()]
    index = start
    while index < len(lines) and index - start < MAX_CONTINUATION_LINES:
        continued = CONTINUATION.match(lines[index])
        if continued is None:
            break
        parts.append(continued.group("text").strip())
        index += 1
    return " ".join(parts), index


def _parse_warning(
    lines: list[str], index: int, current_file: str | None
) -> tuple[list[Finding], int] | None:
    match = WARNING.match(lines[index])
    if match is None:
        return None
    message, next_index = _gather_continuation(lines, index + 1, match.group("message"))
    if WARNING_SUMMARY.match(message):
        return [], next_index
    kind = next((kind for pattern, kind in WARNING_KINDS if pattern.match(message)), Kind.WARNING)
    input_line = INPUT_LINE.search(message)
    finding = Finding(
        kind=kind,
        severity=Severity.WARNING if kind is Kind.WARNING else Severity.DEFECT,
        message=f"{match.group('source')}: {message}",
        file=current_file,
        line=int(input_line.group(1)) if input_line else None,
    )
    return [finding], next_index


def _parse_missing_glyph(
    lines: list[str], index: int, current_file: str | None
) -> tuple[list[Finding], int] | None:
    if MISSING_GLYPH.match(lines[index]) is None:
        return None
    return [Finding(Kind.MISSING_GLYPH, Severity.DEFECT, lines[index], current_file)], index + 1


def parse_bibtex_log(log: bytes) -> list[Finding]:
    """Read a BibTeX `.blg` file: errors are defects, `Warning--` lines warnings."""
    lines = log.decode("utf-8", errors="replace").splitlines()
    findings: list[Finding] = []
    for index, text in enumerate(lines):
        if text.startswith("Warning--"):
            message = text.removeprefix("Warning--")
            findings.append(Finding(Kind.BIBLIOGRAPHY, Severity.WARNING, message))
            continue
        located = BIBTEX_ERROR_LOCATION.match(text)
        if located is not None:
            message = located.group("before") or (lines[index - 1] if index else "")
            file, line = located.group("file"), int(located.group("line"))
            findings.append(Finding(Kind.BIBLIOGRAPHY, Severity.DEFECT, message, file, line))
            continue
        reading = BIBTEX_ERROR_WHILE.match(text)
        if reading is not None:
            message, file = reading.group("message"), reading.group("file")
            findings.append(Finding(Kind.BIBLIOGRAPHY, Severity.DEFECT, message, file))
    return findings


@dataclass(frozen=True, slots=True)
class LatexmkRun:
    exit_code: int | None
    output: str


def engine_flags(engine: Engine | None, folder: Path) -> list[str]:
    """The latexmk option for the engine; none when the folder's latexmkrc decides."""
    if engine is None and any((folder / name).is_file() for name in LATEXMKRC_NAMES):
        return []
    return [ENGINE_FLAGS[engine or DEFAULT_ENGINE]]


def run_latexmk(
    latexmk: str, document: Path, engine: Engine | None, outdir: Path, timeout_seconds: float
) -> LatexmkRun:
    """Run latexmk to completion or until the timeout, killing its whole process tree.

    `exit_code` is None when the timeout stopped the build.
    """
    command = [
        latexmk,
        *engine_flags(engine, document.parent),
        "-g",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-outdir={outdir}",
        document.name,
    ]
    # MiKTeX's BibTeX ignores the search path latexmk sets when the output
    # folder differs from the source folder, so name the source folder here.
    bib_inputs = f"{document.parent}{os.pathsep}{os.environ.get('BIBINPUTS', '')}"
    env = {**os.environ, "BIBINPUTS": bib_inputs}
    exit_code, output = _run_process_tree(command, document.parent, env, timeout_seconds)
    return LatexmkRun(exit_code, output.decode("utf-8", errors="replace"))


def _run_process_tree(
    command: list[str], cwd: Path, env: dict[str, str], timeout_seconds: float
) -> tuple[int | None, bytes]:
    """Run a command, killing it and every process it started if the timeout passes.

    Killing latexmk alone leaves the TeX engine running, holding the log open
    and still writing to the output pipe. On Windows the tree cannot be found by
    parentage either, because MiKTeX starts the engine through a launcher that
    exits, so the command runs inside a job object that holds every descendant.
    """
    pipe, merge, nothing = subprocess.PIPE, subprocess.STDOUT, subprocess.DEVNULL
    if sys.platform == "win32":
        job = _create_job()
        try:
            with subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=nothing,
                stdout=pipe,
                stderr=merge,
                creationflags=CREATE_SUSPENDED,
            ) as process:
                _start_in_job(job, process)
                return _communicate_or_kill(process, timeout_seconds, lambda: _terminate_job(job))
        finally:
            _close_handle(job)
    else:
        with subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=nothing,
            stdout=pipe,
            stderr=merge,
            start_new_session=True,
        ) as process:
            return _communicate_or_kill(process, timeout_seconds, lambda: _kill_group(process.pid))


if sys.platform != "win32":

    def _kill_group(pid: int) -> None:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            return  # the whole group exited between the timeout and the kill


def _communicate_or_kill(
    process: subprocess.Popen[bytes], timeout_seconds: float, kill_tree: Callable[[], None]
) -> tuple[int | None, bytes]:
    try:
        output, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        try:
            kill_tree()
        except OSError:
            # Kill latexmk at least, or leaving the with block waits on it for ever.
            process.kill()
            raise
        output, _ = process.communicate(timeout=KILL_TIMEOUT_SECONDS)
        return None, output
    return process.returncode, output


if sys.platform == "win32":

    def _kernel32() -> ctypes.WinDLL:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        return kernel32

    def _create_job() -> int:
        job = _kernel32().CreateJobObjectW(None, None)
        if not job:
            raise ctypes.WinError(ctypes.get_last_error())
        return int(job)

    def _start_in_job(job: int, process: subprocess.Popen[bytes]) -> None:
        """Move a suspended process into the job, then let it run.

        Starting it suspended means nothing it spawns can escape the job by
        starting before the assignment.
        """
        kernel32 = _kernel32()
        access = PROCESS_SET_QUOTA | PROCESS_TERMINATE | PROCESS_SUSPEND_RESUME
        handle = kernel32.OpenProcess(access, False, process.pid)
        if not handle:
            process.kill()
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not kernel32.AssignProcessToJobObject(job, handle):
                process.kill()
                raise ctypes.WinError(ctypes.get_last_error())
            ntdll = ctypes.WinDLL("ntdll")
            ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
            status = ntdll.NtResumeProcess(handle)
            if status != 0:
                process.kill()
                raise OSError(f"NtResumeProcess failed with status {status:#x}")
        finally:
            _close_handle(handle)

    def _terminate_job(job: int) -> None:
        if not _kernel32().TerminateJobObject(job, 1):
            raise ctypes.WinError(ctypes.get_last_error())

    def _close_handle(handle: int) -> None:
        if not _kernel32().CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def assess(
    run: LatexmkRun, log: bytes | None, bibtex_log: bytes | None, timeout_seconds: float
) -> list[Finding]:
    """Combine log findings with what the latexmk run itself says went wrong."""
    findings = parse_log(log) if log is not None else []
    if bibtex_log is not None:
        findings += parse_bibtex_log(bibtex_log)
    if run.exit_code is None:
        message = (
            f"latexmk stopped after {timeout_seconds:g} s: the document may loop, "
            "or the TeX distribution may still be installing packages"
        )
        return [*findings, Finding(Kind.BUILD, Severity.DEFECT, message)]
    tail = "\n".join(run.output.strip().splitlines()[-FAILURE_TAIL_LINES:])
    if log is None:
        # latexmk failed before TeX ran, as when MiKTeX finds no Perl, so its own
        # output is the only account of why.
        message = f"latexmk wrote no TeX log:\n{tail}" if tail else "latexmk wrote no TeX log"
        findings.append(Finding(Kind.BUILD, Severity.DEFECT, message))
    has_defect = any(finding.severity is Severity.DEFECT for finding in findings)
    if run.exit_code != 0 and not has_defect:
        message = f"latexmk exited with status {run.exit_code}:\n{tail}"
        findings.append(Finding(Kind.BUILD, Severity.DEFECT, message))
    return findings


def format_report(document: Path, engine: str, findings: list[Finding], pdf: Path | None) -> str:
    counts = Counter(findings)
    # A build stopped by an error leaves every later reference and citation
    # undefined, so the error leads and its consequences follow.
    defects = sorted(
        (finding for finding in counts if finding.severity is Severity.DEFECT),
        key=lambda finding: finding.kind not in STOPPING_KINDS,
    )
    warnings = [finding for finding in counts if finding.severity is Severity.WARNING]
    lines = [f"{document.name} ({engine}): {len(defects)} defects, {len(warnings)} warnings"]
    if pdf is not None:
        lines.append(f"PDF: {pdf}")
    for heading, group in (("Defects", defects), ("Warnings", warnings)):
        if group:
            lines += ["", heading, *_format_group(group, counts)]
    return "\n".join(lines)


def _format_group(group: list[Finding], counts: Counter[Finding]) -> list[str]:
    lines: list[str] = []
    shown: Counter[Kind] = Counter()
    for finding in group:
        shown[finding.kind] += 1
        if shown[finding.kind] > MAX_SHOWN_PER_KIND:
            continue
        location = finding.file or "-"
        if finding.line is not None:
            location += f":{finding.line}"
        repeats = f" ({counts[finding]} times)" if counts[finding] > 1 else ""
        lines.append(f"  {finding.kind}  {location}  {finding.message}{repeats}")
    for kind, total in shown.items():
        if total > MAX_SHOWN_PER_KIND:
            lines.append(f"  {kind}: {total - MAX_SHOWN_PER_KIND} more not shown")
    return lines


FileState = tuple[int, int] | None


def file_state(path: Path) -> FileState:
    """Modification time and size, or None when the file is absent."""
    if not path.is_file():
        return None
    status = path.stat()
    return status.st_mtime_ns, status.st_size


def is_rewritten(path: Path, before: FileState) -> bool:
    """Whether the run wrote the file, rather than leaving an earlier build's copy."""
    after = file_state(path)
    return after is not None and after != before


def _read_rewritten(path: Path, before: FileState) -> bytes | None:
    if not is_rewritten(path, before):
        return None
    with path.open("rb") as handle:
        return handle.read(MAX_LOG_BYTES)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("document", type=Path, help="the main .tex file")
    parser.add_argument(
        "--engine",
        type=Engine,
        choices=list(Engine),
        help="default: the folder's latexmkrc, or lualatex without one",
    )
    parser.add_argument("--outdir", type=Path, default=Path("build"))
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    document = args.document.resolve()
    if document.suffix != ".tex" or not document.is_file():
        print(f"expected an existing .tex file, got {args.document}", file=sys.stderr)
        return 2
    if args.timeout_seconds <= 0:
        print(f"expected a positive timeout, got {args.timeout_seconds:g}", file=sys.stderr)
        return 2
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        print("latexmk not found on PATH; install MiKTeX or TeX Live", file=sys.stderr)
        return 2

    if isinstance(sys.stdout, io.TextIOWrapper):
        # Logs quote characters a Windows console code page cannot encode.
        sys.stdout.reconfigure(errors="replace")
    outdir = document.parent / args.outdir
    flags = engine_flags(args.engine, document.parent)
    engine_label = str(args.engine or DEFAULT_ENGINE) if flags else "engine from latexmkrc"
    log_path, bibtex_path, pdf = (outdir / f"{document.stem}{suffix}" for suffix in OUTPUTS)
    before = {path: file_state(path) for path in (bibtex_path, pdf)}
    for suffix in CARRIED_STATE:
        carried = outdir / f"{document.stem}{suffix}"
        try:
            carried.unlink(missing_ok=True)
        except PermissionError:
            print(f"cannot clear {carried}: is another build using it?", file=sys.stderr)
            return 2
    run = run_latexmk(latexmk, document, args.engine, outdir, args.timeout_seconds)
    # The log was cleared with the carried state, so any log is this run's.
    log = _read_rewritten(log_path, before=None)
    bibtex_log = _read_rewritten(bibtex_path, before[bibtex_path])
    findings = assess(run, log, bibtex_log, args.timeout_seconds)
    written_pdf = pdf if is_rewritten(pdf, before[pdf]) else None
    print(format_report(document, engine_label, findings, written_pdf))
    return 1 if any(finding.severity is Severity.DEFECT for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
