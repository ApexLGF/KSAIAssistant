"""Base tool class for TestAIAgent."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for parameters
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result as string
        """
        pass
    
    def to_openai_tool(self) -> dict:
        """Convert to OpenAI function calling format.
        
        Returns:
            Tool definition in OpenAI format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
