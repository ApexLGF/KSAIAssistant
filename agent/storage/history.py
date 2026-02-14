"""History storage for TestAIAgent."""

import json
from pathlib import Path

from agent.core.context import Context


class HistoryStorage:
    """Manages persistent storage of conversation history."""
    
    def __init__(self, history_file: str | Path):
        """Initialize history storage.
        
        Args:
            history_file: Path to history JSON file
        """
        self.history_file = Path(history_file)
    
    def save(self, context: Context) -> None:
        """Save context to file.
        
        Args:
            context: Context to save
        """
        # Ensure directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = context.to_serializable()
        
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self) -> Context | None:
        """Load context from file.
        
        Returns:
            Loaded Context or None if file doesn't exist
        """
        if not self.history_file.exists():
            return None
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Context.from_serializable(data)
        except Exception:
            return None
    
    def clear(self) -> None:
        """Delete the history file."""
        if self.history_file.exists():
            self.history_file.unlink()
