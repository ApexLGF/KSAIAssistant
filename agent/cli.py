"""CLI for TestAIAgent."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from agent.config import load_config
from agent.core.agent import Agent

app = typer.Typer(
    name="agent",
    help="AI Agent with MCP Server, Skills, and Command Execution support",
    invoke_without_command=True,
)
console = Console()

# History file for input history
HISTORY_FILE = Path.home() / ".testagent_input_history"


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(
        None, "-c", "--config",
        help="Path to config file",
    ),
    clear: bool = typer.Option(
        False, "--clear",
        help="Clear history before starting",
    ),
):
    """AI Agent with MCP Server, Skills, and Command Execution support."""
    if ctx.invoked_subcommand is None:
        # No subcommand was provided, run chat
        asyncio.run(_chat_async(config, clear))


def _create_agent(config_path: Optional[str] = None) -> Agent:
    """Create an agent instance."""
    config = load_config(config_path)
    return Agent(config)


@app.command()
def chat(
    config: Optional[str] = typer.Option(
        None, "-c", "--config",
        help="Path to config file",
    ),
    clear: bool = typer.Option(
        False, "--clear",
        help="Clear history before starting",
    ),
):
    """Start an interactive chat session."""
    asyncio.run(_chat_async(config, clear))


async def _chat_async(config_path: Optional[str], clear: bool):
    """Async chat implementation."""
    agent = _create_agent(config_path)
    
    # Create prompt session with history support
    session = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
    )
    
    try:
        await agent.initialize()
        
        if clear:
            agent.clear_history()
        
        console.print("\n[bold green]Chat started.[/] Type [bold]/quit[/] to exit.\n")
        console.print("Commands: [dim]/clear, /tools, /skills, /quit[/]")
        console.print("[dim]Use ↑↓ keys to browse input history[/]\n")
        
        while True:
            try:
                # Use prompt_toolkit for better Unicode and history support
                user_input = await session.prompt_async("You: ")
                user_input = user_input.strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower()
                
                if cmd in ("/quit", "/exit"):
                    break
                elif cmd == "/clear":
                    agent.clear_history()
                    continue
                elif cmd == "/tools":
                    _show_tools(agent)
                    continue
                elif cmd == "/skills":
                    _show_skills(agent)
                    continue
                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/]")
                    continue
            
            # Get response with streaming
            try:
                console.print()
                console.print("[bold green]A:[/]")
                
                # Stream response in real-time
                response = await agent.chat_stream(
                    user_input,
                    on_content=lambda chunk: print(chunk, end="", flush=True),
                )
                
                print()  # New line after streaming
                console.print()
            except Exception as e:
                console.print(f"[red]Error: {e}[/]")
    
    finally:
        await agent.shutdown()
        console.print("\n[dim]Goodbye![/]")


def _show_tools(agent: Agent):
    """Display available tools."""
    tools = agent.list_tools()
    
    if not tools:
        console.print("[dim]No tools available.[/]")
        return
    
    table = Table(title="Available Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    
    for tool in tools:
        table.add_row(tool["name"], tool["description"][:60] + "...")
    
    console.print(table)


def _show_skills(agent: Agent):
    """Display loaded skills."""
    skills = agent.list_skills()
    
    if not skills:
        console.print("[dim]No skills loaded.[/]")
        return
    
    table = Table(title="Loaded Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Description")
    
    for skill in skills:
        table.add_row(skill["name"], skill["type"], skill["description"])
    
    console.print(table)


@app.command()
def tools(
    config: Optional[str] = typer.Option(
        None, "-c", "--config",
        help="Path to config file",
    ),
):
    """List available tools."""
    asyncio.run(_tools_async(config))


async def _tools_async(config_path: Optional[str]):
    """Async tools listing."""
    agent = _create_agent(config_path)
    await agent.initialize()
    _show_tools(agent)
    await agent.shutdown()


@app.command()
def skills(
    config: Optional[str] = typer.Option(
        None, "-c", "--config",
        help="Path to config file",
    ),
):
    """List loaded skills."""
    asyncio.run(_skills_async(config))


async def _skills_async(config_path: Optional[str]):
    """Async skills listing."""
    agent = _create_agent(config_path)
    await agent.initialize()
    _show_skills(agent)
    await agent.shutdown()


if __name__ == "__main__":
    app()
