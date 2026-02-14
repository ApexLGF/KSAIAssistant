"""MCP tool adapter for TestAIAgent."""

from typing import Any

from agent.tools.base import BaseTool
from agent.tools.mcp.manager import MCPManager


class MCPTool(BaseTool):
    """Adapter that wraps an MCP tool as a BaseTool."""
    
    def __init__(
        self,
        manager: MCPManager,
        server_name: str,
        tool_name: str,
        description: str,
        input_schema: dict,
    ):
        """Initialize MCP tool adapter.
        
        Args:
            manager: MCP manager instance
            server_name: Name of the MCP server
            tool_name: Name of the tool on the server
            description: Tool description
            input_schema: JSON Schema for tool parameters
        """
        self._manager = manager
        self._server_name = server_name
        self.name = f"{server_name}__{tool_name}"  # Namespaced name
        self._original_name = tool_name
        self.description = description
        self.parameters = input_schema
    
    async def execute(self, **kwargs: Any) -> str:
        """Execute the MCP tool.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool result
        """
        return await self._manager.call_tool(
            self._server_name,
            self._original_name,
            kwargs,
        )


def create_mcp_tools(manager: MCPManager) -> list[MCPTool]:
    """Create BaseTool instances for all MCP tools.
    
    Args:
        manager: MCP manager with active connections
        
    Returns:
        List of MCPTool instances
    """
    tools = []
    
    for connection in manager.list_connections():
        for tool_info in connection.tools:
            tool = MCPTool(
                manager=manager,
                server_name=connection.name,
                tool_name=tool_info["name"],
                description=tool_info["description"],
                input_schema=tool_info["inputSchema"],
            )
            tools.append(tool)
    
    return tools
