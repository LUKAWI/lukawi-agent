"""Tests for SkillLoader and SKILL.md frontmatter parsing."""

from pathlib import Path

import pytest

from lukawi.skills.loader import SkillLoader


# =============================================================================
# _parse_frontmatter
# =============================================================================

def test_parse_frontmatter_full():
    """Parse content with complete YAML frontmatter."""
    content = """\
---
name: web-search
description: Search the web
triggers:
  - search
  - find
---

This is the instruction content.
"""
    loader = SkillLoader()
    metadata, instructions = loader._parse_frontmatter(content)

    assert metadata["name"] == "web-search"
    assert metadata["description"] == "Search the web"
    assert metadata["triggers"] == ["search", "find"]
    assert instructions == "This is the instruction content."


def test_parse_frontmatter_no_frontmatter():
    """Parse plain text without any frontmatter."""
    content = "Just plain instructions without metadata."
    loader = SkillLoader()
    metadata, instructions = loader._parse_frontmatter(content)

    assert metadata == {}
    assert instructions == "Just plain instructions without metadata."


def test_parse_frontmatter_incomplete():
    """Parse content with only opening --- but no closing ---."""
    content = """\
---
name: broken-skill
no closing delimiter
"""
    loader = SkillLoader()
    metadata, instructions = loader._parse_frontmatter(content)

    assert metadata == {}
    assert instructions == content.strip()


def test_parse_frontmatter_empty_yaml():
    """Parse frontmatter that contains only a comment (yields None from yaml.safe_load)."""
    content = """\
---
# this is just a comment
---

Body text here.
"""
    loader = SkillLoader()
    metadata, instructions = loader._parse_frontmatter(content)

    assert metadata == {}
    assert instructions == "Body text here."


def test_parse_frontmatter_triggers_as_string():
    """Parse frontmatter where triggers is a single string instead of a list."""
    content = """\
---
name: single-trigger
description: A skill with single trigger string
triggers: hello
---

Do something.
"""
    loader = SkillLoader()
    metadata, instructions = loader._parse_frontmatter(content)

    assert metadata["name"] == "single-trigger"
    assert metadata["triggers"] == "hello"
    assert instructions == "Do something."

    # The string-to-list conversion happens in load_skill, not _parse_frontmatter


# =============================================================================
# load_skill
# =============================================================================

def test_load_skill_from_file(tmp_path: Path):
    """Load a skill from a SKILL.md file on disk."""
    skill_dir = tmp_path / "web-search"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""\
---
name: web-search
description: Search the web for information
triggers:
  - search
  - find
---

Use the search engine to find information.
""", encoding="utf-8")

    loader = SkillLoader()
    skill = loader.load_skill(skill_file)

    assert skill.name == "web-search"
    assert skill.description == "Search the web for information"
    assert skill.triggers == ["search", "find"]
    assert skill.instructions == "Use the search engine to find information."
    assert skill.path == skill_file


def test_load_skill_missing_description(tmp_path: Path):
    """Load a skill that has no description field in frontmatter."""
    skill_dir = tmp_path / "no-desc"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""\
---
name: no-desc
triggers:
  - test
---

Just do it.
""", encoding="utf-8")

    loader = SkillLoader()
    skill = loader.load_skill(skill_file)

    assert skill.name == "no-desc"
    assert skill.description == ""
    assert skill.triggers == ["test"]
    assert skill.instructions == "Just do it."


# =============================================================================
# load_directory
# =============================================================================

def test_load_directory_multiple(tmp_path: Path):
    """Scan a directory and load multiple skills."""
    for name in ("alpha", "beta", "gamma"):
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"""\
---
name: {name}
description: Skill {name}
triggers:
  - {name}
---

Instructions for {name}.
""", encoding="utf-8")

    loader = SkillLoader()
    skills = loader.load_directory(tmp_path)

    assert len(skills) == 3
    names = {s.name for s in skills}
    assert names == {"alpha", "beta", "gamma"}


def test_load_directory_not_exists(tmp_path: Path):
    """Call load_directory with a non-existent directory."""
    loader = SkillLoader()
    skills = loader.load_directory(tmp_path / "does-not-exist")

    assert skills == []


def test_load_directory_uses_skills_dir(tmp_path: Path):
    """load_directory uses the skills_dir set at construction when no argument given."""
    d = tmp_path / "myskills"
    d.mkdir()
    (d / "SKILL.md").write_text("""\
---
name: auto-dir
description: Loaded from skills_dir
---

ok
""", encoding="utf-8")

    loader = SkillLoader(skills_dir=d)
    skills = loader.load_directory()

    assert len(skills) == 1
    assert skills[0].name == "auto-dir"


# =============================================================================
# get_skill
# =============================================================================

def test_get_skill_exists(tmp_path: Path):
    """get_skill returns the skill after it has been loaded."""
    skill_dir = tmp_path / "myskill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""\
---
name: my-skill
description: Found me
---

content
""", encoding="utf-8")

    loader = SkillLoader()
    loader.load_skill(skill_file)

    skill = loader.get_skill("my-skill")
    assert skill is not None
    assert skill.name == "my-skill"
    assert skill.description == "Found me"


def test_get_skill_not_exists():
    """get_skill returns None when the skill has not been loaded."""
    loader = SkillLoader()
    skill = loader.get_skill("nobody")

    assert skill is None


# =============================================================================
# list_skills
# =============================================================================

def test_list_skills_empty():
    """list_skills returns an empty list when no skills have been loaded."""
    loader = SkillLoader()
    assert loader.list_skills() == []


def test_list_skills_after_load(tmp_path: Path):
    """list_skills returns all loaded skills after loading."""
    for name in ("a", "b"):
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"""\
---
name: {name}
description: Skill {name}
---

instructions
""", encoding="utf-8")

    loader = SkillLoader()
    loader.load_directory(tmp_path)

    skills = loader.list_skills()
    assert len(skills) == 2
    assert {s.name for s in skills} == {"a", "b"}
