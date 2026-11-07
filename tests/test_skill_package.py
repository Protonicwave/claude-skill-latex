"""The skill folder is a complete package: valid frontmatter, no dangling or orphaned files."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "latex"
SKILL_TEXT = (SKILL / "SKILL.md").read_text(encoding="utf-8")
# Claude Code reads the frontmatter's description to decide when to load the
# skill and truncates it beyond this length.
MAX_DESCRIPTION_CHARS = 1024
FRONTMATTER = re.compile(r"\A---\n(?P<fields>.*?)\n---\n", re.DOTALL)
NAMED_PATH = re.compile(r"`((?:profiles|references|scripts|assets)/[^`\s]+)`")
DASHES = {chr(0x2013): "en dash", chr(0x2014): "em dash"}
MARKDOWN_FILES = sorted(SKILL.rglob("*.md"))


def frontmatter_fields() -> dict[str, str]:
    match = FRONTMATTER.match(SKILL_TEXT)
    assert match is not None, "SKILL.md does not open with a --- frontmatter block"
    fields = {}
    for line in match.group("fields").splitlines():
        key, separator, value = line.partition(":")
        assert separator, f"frontmatter line is not 'key: value': {line!r}"
        fields[key.strip()] = value.strip()
    return fields


def test_frontmatter_names_the_skill_after_its_folder() -> None:
    assert frontmatter_fields()["name"] == SKILL.name


def test_frontmatter_description_fits_the_loader() -> None:
    description = frontmatter_fields()["description"]
    assert 0 < len(description) <= MAX_DESCRIPTION_CHARS


def test_every_file_skill_md_names_exists() -> None:
    named = NAMED_PATH.findall(SKILL_TEXT)
    assert named, "SKILL.md names no skill files"
    missing = [path for path in named if not (SKILL / path).exists()]
    assert missing == []


@pytest.mark.parametrize("folder", ["profiles", "references"])
def test_skill_md_names_every_profile_and_reference(folder: str) -> None:
    named = set(NAMED_PATH.findall(SKILL_TEXT))
    present = {path.relative_to(SKILL).as_posix() for path in (SKILL / folder).glob("*.md")}
    assert present - named == set()


@pytest.mark.parametrize(
    "path", MARKDOWN_FILES, ids=lambda path: path.relative_to(SKILL).as_posix()
)
def test_markdown_has_no_dashes(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    found = [
        f"line {number}: {DASHES[character]}"
        for number, line in enumerate(text.splitlines(), start=1)
        for character in DASHES
        if character in line
    ]
    assert found == []
