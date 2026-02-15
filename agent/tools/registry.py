"""Tool registry for TestAIAgent."""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent.tools.base import BaseTool

if TYPE_CHECKING:
    from agent.tools.skills.loader import SkillLoader


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self, skill_loader: "SkillLoader | None" = None):
        """Initialize the registry.

        Args:
            skill_loader: Optional skill loader for working_dir inference
        """
        self._tools: dict[str, BaseTool] = {}
        self._skill_loader = skill_loader
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool by name.
        
        Args:
            name: Tool name to remove
        """
        self._tools.pop(name, None)
    
    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def list_tools(self) -> list[BaseTool]:
        """Get all registered tools.
        
        Returns:
            List of all tool instances
        """
        return list(self._tools.values())
    
    def get_openai_tools(self) -> list[dict]:
        """Get all tools in OpenAI format.
        
        Returns:
            List of tool definitions for OpenAI API
        """
        return [tool.to_openai_tool() for tool in self._tools.values()]
    
    async def execute(self, name: str, arguments: str | dict) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments (JSON string or dict)

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        if isinstance(arguments, str):
            arguments = json.loads(arguments) if arguments else {}

        # Auto-inject or fix working_dir for run_command
        if name == "run_command":
            inferred = self._infer_working_dir(arguments.get("command", ""))
            if inferred:
                provided = arguments.get("working_dir")
                if not provided or not os.path.isdir(provided):
                    arguments["working_dir"] = inferred

        return await tool.execute(**arguments)

    def _infer_working_dir(self, command: str) -> str | None:
        """Infer working_dir from command content by matching against skills.

        Args:
            command: The shell command string

        Returns:
            Absolute working_dir path if a skill match is found, else None
        """
        if not self._skill_loader or "scripts/run.py" not in command:
            return None
        for skill in self._skill_loader.list_skills():
            # Use working_dir if set, otherwise derive from SKILL.md path
            skill_dir = skill.working_dir or str(Path(skill.path).parent)
            run_py = Path(skill_dir) / "scripts" / "run.py"
            if run_py.is_file():
                return str(Path(skill_dir).resolve())
        return None
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
