"""Tests for the Skills executor (prompt building, skill injection, trigger matching)."""

from lukawi.skills.executor import (
    build_skill_injection,
    build_skill_prompt,
    match_triggers,
)
from lukawi.skills.loader import Skill


def _make_skill(
    name: str = "test_skill",
    description: str = "A test skill",
    triggers: list[str] | None = None,
    instructions: str = "Do the test thing.",
) -> Skill:
    return Skill(
        name=name,
        description=description,
        triggers=triggers or ["test", "verify"],
        instructions=instructions,
    )


def test_build_skill_prompt_empty():
    assert build_skill_prompt([]) == ""


def test_build_skill_prompt_single_skill():
    skill = _make_skill(
        name="translator",
        description="Translate text between languages",
        triggers=["translate", "convert"],
        instructions="Use translation APIs.",
    )
    prompt = build_skill_prompt([skill])
    assert "translator" in prompt
    assert "Translate text" in prompt
    assert "translate" in prompt
    assert "convert" in prompt


def test_build_skill_prompt_triggers_in_output():
    skill = _make_skill(
        name="review",
        description="Code review helper",
        triggers=["review", "audit"],
    )
    prompt = build_skill_prompt([skill])
    assert "review" in prompt
    assert "audit" in prompt


def test_build_skill_prompt_multiple_skills():
    skills = [
        _make_skill(name="s1", description="First", triggers=["a"]),
        _make_skill(name="s2", description="Second", triggers=["b"]),
        _make_skill(name="s3", description="Third", triggers=["c"]),
    ]
    prompt = build_skill_prompt(skills)
    for name in ("s1", "s2", "s3"):
        assert name in prompt


def test_build_skill_prompt_triggers_truncated_at_5():
    skill = _make_skill(
        name="wide",
        description="Has many triggers",
        triggers=["t1", "t2", "t3", "t4", "t5", "t6", "t7"],
    )
    prompt = build_skill_prompt([skill])
    assert "t6" not in prompt
    assert "t7" not in prompt


def test_build_skill_injection_format():
    skill = _make_skill(
        name="formatter",
        description="Format code",
        instructions="Run the formatter.",
    )
    injection = build_skill_injection(skill)
    assert "Active Skill: formatter" in injection
    assert "Format code" in injection
    assert "Run the formatter." in injection


def test_match_triggers_exact_match():
    skill = _make_skill(triggers=["search"])
    matched = match_triggers("can you search for this", [skill])
    assert matched == [skill]


def test_match_triggers_case_insensitive():
    skill = _make_skill(triggers=["search"])
    matched = match_triggers("SEARCH for dogs", [skill])
    assert matched == [skill]


def test_match_triggers_substring():
    skill = _make_skill(triggers=["review"])
    matched = match_triggers("code review please", [skill])
    assert matched == [skill]


def test_match_triggers_no_match():
    skill = _make_skill(triggers=["search"])
    matched = match_triggers("hello world", [skill])
    assert matched == []


def test_match_triggers_multiple_skills():
    skill_a = _make_skill(name="A", triggers=["search"])
    skill_b = _make_skill(name="B", triggers=["find"])
    skill_c = _make_skill(name="C", triggers=["build"])
    matched = match_triggers("help me search and find things", [skill_a, skill_b, skill_c])
    assert len(matched) == 2
    assert skill_a in matched
    assert skill_b in matched
    assert skill_c not in matched


def test_match_triggers_empty_skills_list():
    matched = match_triggers("search for this", [])
    assert matched == []


def test_match_triggers_empty_text():
    skill = _make_skill(triggers=["search"])
    matched = match_triggers("", [skill])
    assert matched == []
