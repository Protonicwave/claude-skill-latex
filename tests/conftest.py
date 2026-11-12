import shutil
import subprocess

import pytest

TEX_TOOLS = ("latexmk", "pdflatex", "lualatex", "pdftoppm", "pdfinfo", "pdftotext")
LATEXMK_CHECK_TIMEOUT_SECONDS = 60


def latexmk_runs() -> bool:
    """Whether latexmk starts: MiKTeX installs it without the Perl it needs."""
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        return False
    try:
        result = subprocess.run(  # noqa: S603 - a fixed command found on PATH
            [latexmk, "-v"],
            capture_output=True,
            timeout=LATEXMK_CHECK_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if not any(item.get_closest_marker("tex") is not None for item in items):
        return
    missing = [tool for tool in TEX_TOOLS if shutil.which(tool) is None]
    if missing:
        reason = f"not on PATH: {', '.join(missing)}"
    elif not latexmk_runs():
        reason = "latexmk does not run; with MiKTeX it needs a Perl on PATH"
    else:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.get_closest_marker("tex") is not None:
            item.add_marker(skip)
