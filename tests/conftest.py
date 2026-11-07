import shutil

import pytest

TEX_TOOLS = ("latexmk", "pdflatex", "lualatex", "pdftoppm", "pdfinfo")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    missing = [tool for tool in TEX_TOOLS if shutil.which(tool) is None]
    if not missing:
        return
    skip = pytest.mark.skip(reason=f"not on PATH: {', '.join(missing)}")
    for item in items:
        if item.get_closest_marker("tex") is not None:
            item.add_marker(skip)
