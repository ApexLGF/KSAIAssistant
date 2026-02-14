"""Tool registry for TestAIAgent."""

import json
from typing import Any

from agent.tools.base import BaseTool


class ToolRegistry:
    """Central registry for all available tools."""
    
    def __init__(self):
        """Initialize the registry."""
        self._tools: dict[str, BaseTool] = {}
    
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
        
        return await tool.execute(**arguments)
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
