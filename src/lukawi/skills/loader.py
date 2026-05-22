"""Skills loader for SKILL.md files."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Skill:
    """A loaded skill definition."""
    name: str
    description: str
    instructions: str
    triggers: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    path: Path | None = None


class SkillLoader:
    """Loader for SKILL.md files with YAML frontmatter."""
    
    def __init__(self, skills_dir: str | Path | None = None):
        """Initialize skill loader.
        
        Args:
            skills_dir: Directory containing skill folders
        """
        self.skills_dir = Path(skills_dir) if skills_dir else None
        self._skills: dict[str, Skill] = {}
    
    def load_skill(self, path: Path) -> Skill:
        """Load a single skill from a SKILL.md file.
        
        Args:
            path: Path to SKILL.md file
        
        Returns:
            Loaded Skill
        """
        content = path.read_text(encoding="utf-8")
        
        # Parse frontmatter and content
        metadata, instructions = self._parse_frontmatter(content)
        
        triggers_raw = metadata.get("triggers", [])
        if isinstance(triggers_raw, str):
            triggers_raw = [triggers_raw]

        skill = Skill(
            name=metadata.get("name", path.parent.name),
            description=metadata.get("description", ""),
            instructions=instructions,
            triggers=triggers_raw,
            metadata=metadata,
            path=path
        )
        
        self._skills[skill.name] = skill
        return skill
    
    def load_directory(self, directory: Path | None = None) -> list[Skill]:
        """Load all skills from a directory.
        
        Args:
            directory: Directory to scan (uses skills_dir if None)
        
        Returns:
            List of loaded skills
        """
        scan_dir = directory or self.skills_dir
        if not scan_dir or not scan_dir.exists():
            return []
        
        skills = []
        
        # Look for SKILL.md files
        for skill_file in scan_dir.rglob("SKILL.md"):
            try:
                skill = self.load_skill(skill_file)
                skills.append(skill)
            except Exception as e:
                logging.warning(f"Failed to load skill from {skill_file}: {e}")
                continue
        
        return skills
    
    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name.
        
        Args:
            name: Skill name
        
        Returns:
            Skill if found, None otherwise
        """
        return self._skills.get(name)
    
    def list_skills(self) -> list[Skill]:
        """List all loaded skills.
        
        Returns:
            List of skills
        """
        return list(self._skills.values())
    
    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content.
        
        Args:
            content: Markdown content with optional frontmatter
        
        Returns:
            Tuple of (metadata dict, content without frontmatter)
        """
        # Check for YAML frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if match:
            try:
                metadata = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                metadata = {}
            instructions = match.group(2).strip()
        else:
            metadata = {}
            instructions = content.strip()
        
        return metadata, instructions
