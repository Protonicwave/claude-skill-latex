"""Start a LaTeX project from a profile skeleton in the Laboratory house style.

Usage:
    python new_project.py PROFILE FOLDER

PROFILE is one of report, labreport, notes, paper, slides or poster. FOLDER is
created if it does not exist and may already hold other files, but nothing in
it is overwritten: if any file the profile needs is already there, nothing is
written at all.

The folder receives the skeleton (main.tex and any chapter files), refs.bib,
the house packages the profile loads, an example figure in figures/ with the
mplstyle files that drew it at the profile's size and the figure helper,
laboratory.py, a latexmkrc that selects the profile's engine and
.vscode/settings.json for LaTeX Workshop.

Exit code 0 means the project was written, 2 means a file was already there or
the folder could not be written. A write that fails part way leaves the files
written before it.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from build import Engine

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LATEXMK_PDF_MODES = {Engine.PDFLATEX: 1, Engine.LUALATEX: 4}
FIGURE_NAME = "figures/pendulum.pdf"
# Every medium's figure is drawn with this style; other media add an overlay of their own name.
BASE_MEDIUM = "document"


@dataclass(frozen=True, slots=True)
class Profile:
    engine: Engine
    # The page the figures are drawn for: it names the example figure and the mplstyle overlay.
    medium: str
    packages: tuple[str, ...]


DOCUMENT_PACKAGES = ("laboratory-base.sty", "laboratory.sty")
BEAMER_PACKAGES = ("laboratory-base.sty", "beamerthemeLaboratory.sty")
PROFILES = {
    "report": Profile(Engine.LUALATEX, BASE_MEDIUM, DOCUMENT_PACKAGES),
    "labreport": Profile(Engine.LUALATEX, BASE_MEDIUM, DOCUMENT_PACKAGES),
    "notes": Profile(Engine.LUALATEX, BASE_MEDIUM, DOCUMENT_PACKAGES),
    "paper": Profile(Engine.PDFLATEX, "journal", ()),
    "slides": Profile(Engine.LUALATEX, "slides", BEAMER_PACKAGES),
    "poster": Profile(
        Engine.LUALATEX, "poster", (*BEAMER_PACKAGES, "beamerthemeLaboratoryPoster.sty")
    ),
}


def project_files(profile_name: str) -> dict[str, bytes]:
    """The files a new project of this profile holds, by path relative to its folder."""
    profile = PROFILES[profile_name]
    skeleton = ASSETS / "skeletons" / profile_name
    files = {
        path.relative_to(skeleton).as_posix(): path.read_bytes()
        for path in sorted(skeleton.rglob("*"))
        if path.is_file()
    }
    files["refs.bib"] = (ASSETS / "refs.bib").read_bytes()
    for package in profile.packages:
        files[package] = (ASSETS / package).read_bytes()
    styles = ["laboratory"] if profile.medium == BASE_MEDIUM else ["laboratory", profile.medium]
    for style in styles:
        files[f"figures/{style}.mplstyle"] = (
            ASSETS / "mplstyle" / f"{style}.mplstyle"
        ).read_bytes()
    files["figures/laboratory.py"] = (ASSETS / "mplstyle" / "laboratory.py").read_bytes()
    files[FIGURE_NAME] = (ASSETS / "figures" / f"{profile.medium}.pdf").read_bytes()
    engine_line = f"$pdf_mode = {LATEXMK_PDF_MODES[profile.engine]};  # {profile.engine}\n"
    files["latexmkrc"] = engine_line.encode("utf-8") + (ASSETS / "latexmkrc").read_bytes()
    files[".vscode/settings.json"] = (ASSETS / "vscode-settings.json").read_bytes()
    return files


def write_files(folder: Path, files: dict[str, bytes]) -> None:
    for name, content in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("profile", choices=list(PROFILES))
    parser.add_argument("folder", type=Path, help="the project folder, created if absent")
    args = parser.parse_args(argv)

    folder = args.folder.resolve()
    files = project_files(args.profile)
    clashes = [name for name in files if (folder / name).exists()]
    if clashes:
        print(f"{folder} already holds {', '.join(clashes)}; nothing written", file=sys.stderr)
        return 2
    try:
        write_files(folder, files)
    except OSError as error:
        print(f"could not write the project in {folder}: {error}", file=sys.stderr)
        return 2

    engine = PROFILES[args.profile].engine
    build = Path(__file__).with_name("build.py")
    print(f"{args.profile} project in {folder}: {len(files)} files")
    print(f"Build: python {build} {folder / 'main.tex'} --engine {engine}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
