"""SKILL.md parser for TestAIAgent."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Skill:
    """Represents a parsed skill."""

    name: str
    description: str
    skill_type: str  # "knowledge" or "command"
    content: str  # Markdown content after frontmatter
    path: str  # Path to SKILL.md file
    command: str | None = None  # Shell command for command-type skills
    parameters: dict | None = None  # Parameters schema for command-type skills
    working_dir: str | None = None  # Working directory for commands


def parse_skill_file(file_path: str, content: str) -> Skill:
    """Parse a SKILL.md file.
    
    Args:
        file_path: Path to the SKILL.md file
        content: File content
        
    Returns:
        Parsed Skill object
        
    Raises:
        ValueError: If frontmatter is missing or invalid
    """
    # Split frontmatter and content
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        raise ValueError(f"Invalid SKILL.md format in {file_path}: missing frontmatter")
    
    frontmatter_str = match.group(1)
    markdown_content = match.group(2).strip()
    
    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter in {file_path}: {e}")
    
    if not isinstance(frontmatter, dict):
        raise ValueError(f"Frontmatter must be a YAML object in {file_path}")
    
    # Extract required fields
    name = frontmatter.get("name")
    if not name:
        raise ValueError(f"Missing 'name' in frontmatter of {file_path}")
    
    description = frontmatter.get("description", "")
    skill_type = frontmatter.get("type", "knowledge")
    
    if skill_type not in ("knowledge", "command"):
        raise ValueError(
            f"Invalid skill type '{skill_type}' in {file_path}. "
            "Must be 'knowledge' or 'command'."
        )

    # For command-type skills, extract command and parameters
    command = None
    parameters = None
    if skill_type == "command":
        command = frontmatter.get("command")
        if not command:
            raise ValueError(f"Command-type skill must have 'command' field in {file_path}")

        # Get parameters schema (optional)
        parameters = frontmatter.get("parameters", {
            "type": "object",
            "properties": {},
            "required": []
        })

    # Get working_dir and resolve to absolute path
    working_dir = frontmatter.get("working_dir")
    if working_dir:
        # Resolve relative paths based on SKILL.md location
        skill_dir = Path(file_path).parent
        if working_dir == ".":
            # Current directory (where SKILL.md is)
            working_dir = str(skill_dir.resolve())
        elif working_dir.startswith("./"):
            # Relative to SKILL.md directory, "./" means current dir
            # "./foo" means skill_dir/foo, "./" alone means skill_dir
            relative_part = working_dir[2:]
            if relative_part:
                working_dir = str((skill_dir / relative_part).resolve())
            else:
                working_dir = str(skill_dir.resolve())
        elif working_dir.startswith("~/"):
            working_dir = os.path.expanduser(working_dir)
        elif not os.path.isabs(working_dir):
            working_dir = str((skill_dir / working_dir).resolve())

    return Skill(
        name=name,
        description=description,
        skill_type=skill_type,
        content=markdown_content,
        path=file_path,
        command=command,
        parameters=parameters,
        working_dir=working_dir,
    )
