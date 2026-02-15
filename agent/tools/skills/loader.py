"""Skill loader for TestAIAgent."""

import json
import re
from pathlib import Path

from rich.console import Console

from agent.tools.skills.parser import Skill, parse_skill_file

console = Console()


class SkillLoader:
    """Loads and manages skills from a directory."""

    def __init__(self, skills_dir: str | Path):
        """Initialize the skill loader.

        Args:
            skills_dir: Path to skills directory
        """
        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, Skill] = {}

    def load_all(self) -> list[Skill]:
        """Load all skills from the skills directory.

        Returns:
            List of loaded skills
        """
        self._skills.clear()

        if not self.skills_dir.exists():
            console.print(f"[dim]Skills directory not found: {self.skills_dir}[/]")
            return []

        # Find all SKILL.md files
        skill_files = list(self.skills_dir.rglob("SKILL.md"))

        for skill_file in skill_files:
            try:
                content = skill_file.read_text(encoding="utf-8")
                skill = parse_skill_file(str(skill_file), content)
                self._skills[skill.name] = skill
                console.print(f"[dim]Loaded skill: {skill.name}[/]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load {skill_file}: {e}[/]")

        return list(self._skills.values())

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name.

        Args:
            name: Skill name

        Returns:
            Skill or None if not found
        """
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        """Get all loaded skills.

        Returns:
            List of all skills
        """
        return list(self._skills.values())

    def _get_skill_state(self, skill: Skill) -> str | None:
        """Get dynamic state for a skill if available.

        Args:
            skill: The skill to get state for

        Returns:
            State string or None
        """
        skill_dir = skill.working_dir or str(Path(skill.path).parent)
        return self._get_skill_state_from_dir(skill_dir)

    @staticmethod
    def _get_skill_state_from_dir(skill_dir: str) -> str | None:
        """Get dynamic state from a skill directory.

        Args:
            skill_dir: Absolute path to the skill directory

        Returns:
            State string or None
        """

        # Check for data/library.json (notebooklm style)
        library_path = Path(skill_dir) / "data" / "library.json"
        if library_path.exists():
            try:
                data = json.loads(library_path.read_text(encoding="utf-8"))
                active_id = data.get("active_notebook_id")
                notebooks = data.get("notebooks", {})

                if active_id and active_id in notebooks:
                    nb = notebooks[active_id]
                    return (
                        f"**Current Active Notebook:** `{active_id}`\n"
                        f"- Name: {nb.get('name', 'Unknown')}\n"
                        f"- URL: {nb.get('url', 'Unknown')}\n"
                        f"- Description: {nb.get('description', 'No description')}\n"
                        f"\n(Use `--notebook-id {active_id}` or omit notebook parameter to use this notebook)"
                    )
                elif notebooks:
                    return f"**Available Notebooks:** {', '.join(notebooks.keys())}\n(No active notebook set)"
            except Exception:
                pass

        return None

    def get_knowledge_prompt(self) -> str:
        """Get combined knowledge content for system prompt.

        Returns:
            Combined markdown content from all knowledge skills
        """
        knowledge_skills = [
            skill for skill in self._skills.values()
            if skill.skill_type == "knowledge"
        ]

        if not knowledge_skills:
            return ""

        parts = ["## Skills Knowledge\n"]

        for skill in knowledge_skills:
            parts.append(f"### {skill.name}\n")
            if skill.description:
                parts.append(f"{skill.description}\n")

            # Resolve skill directory: use working_dir if set, otherwise derive from SKILL.md path
            skill_dir = skill.working_dir or str(Path(skill.path).parent)

            parts.append(f"\n**This skill is installed and ready at `{skill_dir}`.**\n")

            # Add dynamic state if available
            state = self._get_skill_state(skill)
            if state:
                parts.append(f"\n{state}\n")

            # Rewrite relative script paths to absolute paths so commands
            # work regardless of working_dir
            content = self._rewrite_paths(skill.content, skill_dir)

            parts.append(f"\n{content}\n")

        return "\n".join(parts)

    @staticmethod
    def _rewrite_paths(content: str, working_dir: str) -> str:
        """Rewrite relative script paths in skill content to absolute paths.

        Converts patterns like `python scripts/run.py ...` to
        `python /absolute/path/scripts/run.py ...` so commands work
        from any working directory. Also replaces default upstream
        install paths with the actual skill location.
        """
        # Rewrite "python scripts/" to "python /abs/path/scripts/"
        content = re.sub(
            r'python\s+scripts/',
            f'python {working_dir}/scripts/',
            content,
        )
        # Replace upstream default paths (e.g. ~/.claude/skills/notebooklm/)
        content = re.sub(
            r'~/.claude/skills/notebooklm/?',
            f'{working_dir}/',
            content,
        )
        return content

    def get_command_skills(self) -> list[Skill]:
        """Get all command-type skills.

        Returns:
            List of command skills
        """
        return [
            skill for skill in self._skills.values()
            if skill.skill_type == "command"
        ]
