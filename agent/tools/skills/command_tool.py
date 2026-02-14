"""Skill command tool wrapper for TestAIAgent."""

import asyncio
import shlex
from typing import Any

from agent.tools.base import BaseTool
from agent.tools.skills.parser import Skill


class SkillCommandTool(BaseTool):
    """Wraps a command-type skill as an executable tool."""

    def __init__(self, skill: Skill):
        """Initialize the skill command tool.

        Args:
            skill: Command-type skill to wrap

        Raises:
            ValueError: If skill is not a command type
        """
        if skill.skill_type != "command":
            raise ValueError(f"Skill {skill.name} is not a command type")

        if not skill.command:
            raise ValueError(f"Skill {skill.name} has no command defined")

        self.skill = skill
        self.name = skill.name
        self.description = skill.description
        self.parameters = skill.parameters or {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs: Any) -> str:
        """Execute the skill command with given parameters.

        Args:
            **kwargs: Parameters to pass to the command

        Returns:
            Command execution result
        """
        # Build command with parameter substitution
        command = self.skill.command

        # Replace {param_name} placeholders with actual values
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                # Properly escape the value for shell
                escaped_value = shlex.quote(str(value))
                command = command.replace(placeholder, escaped_value)

        # Execute the command
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                return f"Command failed with exit code {process.returncode}:\n{error_msg}"

            return stdout.decode().strip()

        except Exception as e:
            return f"Error executing command: {e}"
