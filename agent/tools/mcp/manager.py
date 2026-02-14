"""MCP Server lifecycle manager for TestAIAgent."""

from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from agent.config import MCPServerConfig


@dataclass
class MCPConnection:
    """Represents an active MCP server connection."""
    
    name: str
    session: ClientSession
    tools: list[dict] = field(default_factory=list)
    exit_stack: AsyncExitStack | None = None


class MCPManager:
    """Manages MCP server connections and lifecycle."""
    
    def __init__(self):
        """Initialize the MCP manager."""
        self._connections: dict[str, MCPConnection] = {}
    
    async def connect(self, config: MCPServerConfig) -> MCPConnection:
        """Connect to an MCP server.
        
        Args:
            config: MCP server configuration
            
        Returns:
            Active MCP connection
            
        Raises:
            ValueError: If transport type is not supported
        """
        if config.transport == "stdio":
            return await self._connect_stdio(config)
        elif config.transport == "sse":
            return await self._connect_sse(config)
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")
    
    async def _connect_stdio(self, config: MCPServerConfig) -> MCPConnection:
        """Connect via stdio transport.
        
        Args:
            config: Server configuration
            
        Returns:
            Active connection
        """
        if not config.command:
            raise ValueError(f"No command specified for stdio server: {config.name}")
        
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
        )
        
        # Use AsyncExitStack for proper lifecycle management
        exit_stack = AsyncExitStack()
        
        # Enter stdio client context
        read_stream, write_stream = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        # Enter session context
        session = await exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        
        # Initialize
        await session.initialize()
        
        # Get available tools
        tools_result = await session.list_tools()
        tools = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]
        
        connection = MCPConnection(
            name=config.name,
            session=session,
            tools=tools,
            exit_stack=exit_stack,
        )
        
        self._connections[config.name] = connection
        return connection
    
    async def _connect_sse(self, config: MCPServerConfig) -> MCPConnection:
        """Connect via SSE transport.
        
        Args:
            config: Server configuration
            
        Returns:
            Active connection
        """
        if not config.url:
            raise ValueError(f"No URL specified for SSE server: {config.name}")
        
        # Use AsyncExitStack for proper lifecycle management
        exit_stack = AsyncExitStack()
        
        # Enter SSE client context
        read_stream, write_stream = await exit_stack.enter_async_context(
            sse_client(config.url)
        )
        
        # Enter session context
        session = await exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        
        # Initialize
        await session.initialize()
        
        # Get available tools
        tools_result = await session.list_tools()
        tools = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]
        
        connection = MCPConnection(
            name=config.name,
            session=session,
            tools=tools,
            exit_stack=exit_stack,
        )
        
        self._connections[config.name] = connection
        return connection
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict,
    ) -> str:
        """Call a tool on an MCP server.
        
        Args:
            server_name: Name of the connected server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result as string
            
        Raises:
            ValueError: If server not connected
        """
        connection = self._connections.get(server_name)
        if not connection:
            raise ValueError(f"Server not connected: {server_name}")
        
        result = await connection.session.call_tool(tool_name, arguments)
        
        # Extract text content from result
        if result.content:
            texts = []
            for item in result.content:
                if hasattr(item, "text"):
                    texts.append(item.text)
            return "\n".join(texts)
        
        return ""
    
    def get_connection(self, name: str) -> MCPConnection | None:
        """Get a connection by name."""
        return self._connections.get(name)
    
    def list_connections(self) -> list[MCPConnection]:
        """Get all active connections."""
        return list(self._connections.values())
    
    async def disconnect(self, name: str) -> None:
        """Disconnect from a server.
        
        Args:
            name: Server name to disconnect
        """
        connection = self._connections.pop(name, None)
        if connection and connection.exit_stack:
            try:
                await connection.exit_stack.aclose()
            except BaseException:
                pass  # Ignore ALL errors during cleanup (including CancelledError)
    
    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for name in list(self._connections.keys()):
            try:
                await self.disconnect(name)
            except BaseException:
                pass  # Ignore disconnection errors
