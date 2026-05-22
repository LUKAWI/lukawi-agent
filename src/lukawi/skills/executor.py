"""Skill injection and trigger matching.

Two invocation modes:
1. **Explicit**: `/skill load <name>` TUI command loads full instructions
2. **Implicit**: `match_triggers()` checks user input against trigger keywords
"""

from __future__ import annotations

import re
from lukawi.skills.loader import Skill


def build_skill_prompt(skills: list[Skill]) -> str:
    """Build a skills index into the system prompt.

    Only the name and description are listed (index).
    Full instructions load on demand via explicit /skill command.

    Skills are NOT callable tools — they are behavioral guidelines that
    activate when user input matches their trigger keywords.

    Args:
        skills: List of loaded skills

    Returns:
        Skills index prompt section, empty string if none
    """
    if not skills:
        return ""
    sections = [
        "\n\n## Available Skills",
        "(Skills are NOT tools — they are behavioral guidelines that activate when user input matches their trigger keywords.)\n"
    ]
    for s in skills:
        tags = ", ".join(s.triggers[:5]) if s.triggers else ""
        hint = f" [triggers: {tags}]" if tags else ""
        sections.append(f"- Skill: {s.name}{hint} — {s.description}")
    sections.append(
        "\nTo fulfill a skill, use one of the available tools listed above (e.g. web_fetch, file_ops, shell)."
    )
    return "\n".join(sections).strip()


def build_skill_injection(skill: Skill) -> str:
    """Build full instructions for an explicitly loaded skill.

    Args:
        skill: The skill to inject

    Returns:
        Full skill text for injection into conversation
    """
    parts = [
        f"\n## Active Skill: {skill.name}",
        f"Description: {skill.description}",
        "",
        skill.instructions,
    ]
    return "\n".join(parts)


def match_triggers(text: str, skills: list[Skill]) -> list[Skill]:
    """Match user input against skill triggers (case-insensitive).

    Each skill's trigger list is checked; if any trigger appears
    in the input, the skill is considered a match.

    Args:
        text: User input message
        skills: All loaded skills

    Returns:
        List of skills whose triggers matched
    """
    text_lower = text.lower()
    matched = []
    for skill in skills:
        for trigger in skill.triggers:
            pattern = re.escape(trigger.lower())
            if re.search(pattern, text_lower):
                matched.append(skill)
                break
    return matched
