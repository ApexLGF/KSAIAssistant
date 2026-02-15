"""Main Agent class for TestAIAgent."""

import json
from typing import Any, AsyncIterator, Awaitable, Callable

from rich.console import Console
from rich.markdown import Markdown

from agent.config import Config
from agent.core.context import Context
from agent.core.llm import LLMClient
from agent.storage.history import HistoryStorage
from agent.tools.command import CommandTool
from agent.tools.mcp.client import create_mcp_tools
from agent.tools.mcp.manager import MCPManager
from agent.tools.registry import ToolRegistry
from agent.tools.skills.loader import SkillLoader
from agent.tools.skills.command_parser import skill_command_parser
from agent.tools.skills.cron_manager import cron_manager
from agent.tools.skills.command_tool import SkillCommandTool

console = Console()


class Agent:
    """Main Agent that orchestrates conversation and tool execution."""
    
    DEFAULT_SYSTEM_PROMPT = """You are a helpful sales assistant for Everlasting Cabinetry LLC.

Your primary role is to help customers with:
- Product information and specifications
- Order inquiries and status
- Warranty and return policies
- After-sales service questions
- Company policies and terms

CRITICAL: To answer customer questions, you MUST use the NotebookLM skill by running commands via run_command tool.
The NotebookLM skill IS available and working. DO NOT check if it's available - just use it directly.

To query information, use this exact pattern:
- Tool: run_command
- command: python scripts/run.py ask_question.py --question "your question here"
- working_dir: (use the working directory specified in the NotebookLM skill section below)

Always query NotebookLM FIRST before answering any customer question about the company, products, or policies.

IMPORTANT: When responding to customers:
- Provide information directly and naturally
- DO NOT mention NotebookLM, knowledge base, documentation, or any internal tools
- DO NOT say phrases like "according to the documentation" or "let me check"
- Answer as if you naturally know this information as part of your role
- Be professional, friendly, and concise"""
    
    def __init__(self, config: Config):
        """Initialize the Agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.llm = LLMClient(config.openai, config.deepseek)
        self.registry = ToolRegistry()
        self.mcp_manager = MCPManager()
        self.skill_loader = SkillLoader(config.skills_dir)
        self.storage = HistoryStorage(config.history_file)
        self.context: Context | None = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the agent, loading tools and skills."""
        if self._initialized:
            return
        
        console.print("[dim]Initializing agent...[/]")
        
        # Register built-in tools
        self.registry.register(CommandTool())
        
        # Connect to MCP servers
        for mcp_config in self.config.mcp_servers:
            try:
                console.print(f"[dim]Connecting to MCP server: {mcp_config.name}[/]")
                await self.mcp_manager.connect(mcp_config)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to connect to {mcp_config.name}: {e}[/]")
        
        # Register MCP tools
        mcp_tools = create_mcp_tools(self.mcp_manager)
        for tool in mcp_tools:
            self.registry.register(tool)
        
        # Load skills
        self.skill_loader.load_all()

        # Register command-type skills as tools
        for skill in self.skill_loader.get_command_skills():
            try:
                skill_tool = SkillCommandTool(skill)
                self.registry.register(skill_tool)
                console.print(f"[dim]Registered command skill: {skill.name}[/]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to register skill {skill.name}: {e}[/]")

        # Build system prompt
        system_prompt = self.DEFAULT_SYSTEM_PROMPT
        knowledge = self.skill_loader.get_knowledge_prompt()
        if knowledge:
            system_prompt += f"\n\n{knowledge}"
        
        # Load or create context
        saved_context = self.storage.load()
        if saved_context:
            self.context = saved_context
            self.context.system_prompt = system_prompt
            console.print("[dim]Restored conversation history[/]")
        else:
            self.context = Context(
                system_prompt=system_prompt,
                max_messages=self.config.max_history_messages,
            )
        
        self._initialized = True
        console.print(f"[green]Agent ready. {len(self.registry)} tools available.[/]")
    
    async def chat_stream(
        self,
        user_input: str,
        on_content: Callable[[str], None] | None = None,
        on_tool_call: Callable[[str, dict, str, str], Awaitable[None]] | None = None,
    ) -> str:
        """Process a user message with streaming response.

        Args:
            user_input: User's message
            on_content: Callback for each content chunk
            on_tool_call: Async callback for tool call events (name, args, status, result)

        Returns:
            Complete response content
        """
        if not self._initialized:
            await self.initialize()

        # Validate and fix any incomplete tool call sequences from previous sessions
        if self.context.validate_and_fix():
            console.print("[yellow]Fixed incomplete tool call sequence in history[/]")
            self.storage.save(self.context)

        # Add user message
        self.context.add_user_message(user_input)
        
        # Get tools in OpenAI format
        tools = self.registry.get_openai_tools() if len(self.registry) > 0 else None
        
        # Run conversation loop
        while True:
            # Call LLM with streaming
            result = await self.llm.chat_stream(
                messages=self.context.get_messages(),
                tools=tools,
                on_content=on_content,
            )
            
            # Check for tool calls
            if result.tool_calls:
                # Add assistant message with tool calls
                self.context.add_assistant_message(
                    content=result.content if result.content else None,
                    tool_calls=result.tool_calls,
                )
                
                # Execute each tool call
                for tool_call in result.tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]

                    console.print(f"\n[bold blue]Tool:[/] {tool_name}")
                    console.print(f"[dim]Args: {tool_args}[/]")

                    # Notify tool call started
                    if on_tool_call:
                        try:
                            args_dict = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
                        except json.JSONDecodeError:
                            args_dict = {"raw": tool_args}
                        await on_tool_call(tool_name, args_dict, "started", "")

                    try:
                        tool_result = await self.registry.execute(tool_name, tool_args)
                    except Exception as e:
                        tool_result = f"Error: {e}"

                    console.print(f"[dim]Result: {tool_result[:200]}{'...' if len(tool_result) > 200 else ''}[/]")

                    # Notify tool call completed
                    if on_tool_call:
                        await on_tool_call(tool_name, args_dict, "completed", tool_result)

                    # Add tool result
                    self.context.add_tool_result(
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                        content=tool_result,
                    )
                
                # Continue loop to get next response
                continue
            
            # No tool calls - we have a final response
            if result.content:
                self.context.add_assistant_message(content=result.content)
                self.storage.save(self.context)
                
                # Parse and execute any skill commands in the response
                command_result = self._handle_skill_commands(result.content)
                
                if command_result:
                    # Skill command was executed, inject result and continue conversation
                    self.context.add_user_message(f"[System Response]\n{command_result}")
                    continue  # Get next LLM response with the command result
                
                return result.content
            else:
                return ""
    
    async def chat(self, user_input: str) -> str:
        """Process a user message and return the response (non-streaming).
        
        Args:
            user_input: User's message
            
        Returns:
            Agent's response
        """
        # Use streaming internally but don't print chunks
        return await self.chat_stream(user_input, on_content=None)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        if self.context:
            self.context.clear()
        self.storage.clear()
        console.print("[yellow]Conversation history cleared.[/]")
    
    def list_tools(self) -> list[dict]:
        """Get list of available tools.
        
        Returns:
            List of tool info dicts
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self.registry.list_tools()
        ]
    
    def list_skills(self) -> list[dict]:
        """Get list of loaded skills.
        
        Returns:
            List of skill info dicts
        """
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "type": skill.skill_type,
            }
            for skill in self.skill_loader.list_skills()
        ]
    
    def _handle_skill_commands(self, response: str) -> str | None:
        """Parse and execute skill commands in the response.
        
        Args:
            response: LLM response text
            
        Returns:
            Command execution result to inject back, or None if no commands
        """
        commands = skill_command_parser.parse(response)
        
        if not commands:
            return None
        
        results = []
        
        for cmd in commands:
            console.print(f"\n[bold magenta]━━━ Skill Command Detected ━━━[/]")
            console.print(f"[bold cyan]Type:[/] {cmd.command_type}")
            
            if cmd.command_type == "CRON_CREATE":
                # Parse and execute CRON_CREATE
                cron_data = skill_command_parser.parse_cron_create(cmd.content or "")
                console.print("[bold cyan]Details:[/]")
                for key, value in cron_data.items():
                    console.print(f"  [yellow]{key}:[/] {value}")
                
                # Execute the command
                result = cron_manager.create_job(
                    name=cron_data.get("name", "Unnamed Task"),
                    schedule=cron_data.get("schedule", "* * * * *"),
                    schedule_description=cron_data.get("schedule_description", ""),
                    message=cron_data.get("message", ""),
                )
                console.print(f"[green]{result}[/]")
                results.append(result)
            
            elif cmd.command_type == "CRON_DELETE":
                job_id = cmd.args or ""
                console.print(f"[bold cyan]Job ID:[/] {job_id}")
                
                # Execute the command
                result = cron_manager.delete_job(job_id)
                console.print(f"[yellow]{result}[/]")
                results.append(result)
            
            elif cmd.command_type == "CRON_LIST":
                console.print("[dim]Listing scheduled tasks...[/]")
                
                # Execute the command
                result = cron_manager.list_jobs()
                console.print(f"[dim]{result}[/]")
                results.append(result)
            
            console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")
        
        return "\n".join(results) if results else None
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        await self.mcp_manager.disconnect_all()
        if self.context:
            self.storage.save(self.context)

