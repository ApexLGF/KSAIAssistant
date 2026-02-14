"""Skill command parser for TestAIAgent.

Parses special command tags in LLM responses like:
- [CRON_CREATE]...[/CRON_CREATE]
- [CRON_LIST]
- [CRON_DELETE: <job-id>]
"""

import re
from dataclasses import dataclass


@dataclass
class SkillCommand:
    """A parsed skill command."""
    
    command_type: str  # e.g., "CRON_CREATE", "CRON_LIST", "CRON_DELETE"
    content: str | None = None  # Content between tags (for block commands)
    args: str | None = None  # Arguments (for inline commands like CRON_DELETE)
    raw: str = ""  # Original matched text


class SkillCommandParser:
    """Parser for skill command tags in LLM responses."""
    
    # Block command pattern: [COMMAND_NAME]...[/COMMAND_NAME]
    BLOCK_PATTERN = re.compile(
        r'\[([A-Z_]+)\](.*?)\[/\1\]',
        re.DOTALL
    )
    
    # Inline command pattern: [COMMAND_NAME] or [COMMAND_NAME: args]
    INLINE_PATTERN = re.compile(
        r'\[([A-Z_]+)(?::\s*([^\]]+))?\]'
    )
    
    # Known command types
    KNOWN_COMMANDS = {
        "CRON_CREATE",
        "CRON_LIST", 
        "CRON_DELETE",
    }
    
    def parse(self, text: str) -> list[SkillCommand]:
        """Parse all skill commands from text.
        
        Args:
            text: LLM response text
            
        Returns:
            List of parsed SkillCommand objects
        """
        commands = []
        
        # First find block commands
        for match in self.BLOCK_PATTERN.finditer(text):
            cmd_type = match.group(1)
            if cmd_type in self.KNOWN_COMMANDS:
                commands.append(SkillCommand(
                    command_type=cmd_type,
                    content=match.group(2).strip(),
                    raw=match.group(0),
                ))
        
        # Find positions of block commands to exclude them from inline search
        block_positions = set()
        for match in self.BLOCK_PATTERN.finditer(text):
            for i in range(match.start(), match.end()):
                block_positions.add(i)
        
        # Then find inline commands (not inside block commands)
        for match in self.INLINE_PATTERN.finditer(text):
            # Skip if this match is inside a block command
            if match.start() in block_positions:
                continue
            
            cmd_type = match.group(1)
            if cmd_type in self.KNOWN_COMMANDS:
                # Skip if this is actually a block command opening tag
                closing_tag = f"[/{cmd_type}]"
                if closing_tag in text[match.end():]:
                    continue
                
                commands.append(SkillCommand(
                    command_type=cmd_type,
                    args=match.group(2).strip() if match.group(2) else None,
                    raw=match.group(0),
                ))
        
        return commands
    
    def parse_cron_create(self, content: str) -> dict[str, str]:
        """Parse CRON_CREATE content into key-value pairs.
        
        Args:
            content: Content between [CRON_CREATE] and [/CRON_CREATE]
            
        Returns:
            Dict with keys: name, schedule, schedule_description, message
        """
        result = {}
        current_key = None
        current_value_lines = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new key
            if ':' in line:
                key_part = line.split(':', 1)[0].strip().lower()
                if key_part in ('name', 'schedule', 'schedule_description', 'message'):
                    # Save previous key-value
                    if current_key:
                        result[current_key] = '\n'.join(current_value_lines).strip()
                    
                    current_key = key_part
                    current_value_lines = [line.split(':', 1)[1].strip()]
                    continue
            
            # Continuation of current value
            if current_key:
                current_value_lines.append(line)
        
        # Save last key-value
        if current_key:
            result[current_key] = '\n'.join(current_value_lines).strip()
        
        return result


# Global parser instance
skill_command_parser = SkillCommandParser()
