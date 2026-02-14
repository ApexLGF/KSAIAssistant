"""Shell command execution tool for TestAIAgent."""

import asyncio
import os
import subprocess

from rich.console import Console
from rich.prompt import Confirm

from agent.tools.base import BaseTool

console = Console()

# Default timeout for commands (5 minutes)
DEFAULT_TIMEOUT = 300


class CommandTool(BaseTool):
    """Tool for executing shell commands with user confirmation."""

    name = "run_command"
    description = "Execute a shell command on the local system. The user will be prompted to confirm before execution."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory for the command (optional)",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 300, max 600)",
            },
        },
        "required": ["command"],
    }

    def __init__(self, auto_confirm: bool = True):
        """Initialize command tool.

        Args:
            auto_confirm: If True, skip user confirmation
        """
        self.auto_confirm = auto_confirm

    async def execute(
        self,
        command: str,
        working_dir: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Execute a shell command.

        Args:
            command: Shell command to execute
            working_dir: Optional working directory
            timeout: Optional timeout in seconds (default 300, max 600)

        Returns:
            Command output or error message
        """
        # Display command to user
        console.print(f"\n[bold yellow]Command:[/] {command}")
        if working_dir:
            console.print(f"[dim]Working dir: {working_dir}[/]")

        # Get user confirmation
        if not self.auto_confirm:
            confirmed = Confirm.ask(
                "[bold]Execute this command?[/]",
                default=False,
            )
            if not confirmed:
                return "Command execution cancelled by user."

        # Set timeout (default 300s, max 600s)
        cmd_timeout = min(timeout or DEFAULT_TIMEOUT, 600)

        # Execute command
        try:
            # Expand ~ in working_dir
            cwd = os.path.expanduser(working_dir) if working_dir else None

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=cmd_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Command timed out after {cmd_timeout} seconds"

            output_parts = []

            if stdout:
                output_parts.append(f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}")

            if stderr:
                output_parts.append(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}")

            if process.returncode != 0:
                output_parts.append(f"Exit code: {process.returncode}")

            return "\n".join(output_parts) if output_parts else "Command completed with no output."

        except Exception as e:
            return f"Error executing command: {e}"
