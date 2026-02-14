"""Context and message management for TestAIAgent."""

from dataclasses import dataclass, field


@dataclass
class Message:
    """A single message in the conversation."""
    
    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None  # Tool name for tool messages
    
    def to_dict(self) -> dict:
        """Convert to OpenAI message format."""
        msg = {"role": self.role}
        
        if self.content is not None:
            msg["content"] = self.content
        
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        
        if self.name:
            msg["name"] = self.name
        
        return msg
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data.get("content"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
        )


@dataclass
class Context:
    """Manages conversation context and messages."""
    
    system_prompt: str = ""
    messages: list[Message] = field(default_factory=list)
    max_messages: int = 500
    
    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.messages.append(Message(role="user", content=content))
        self._trim_messages()
    
    def add_assistant_message(
        self,
        content: str | None = None,
        tool_calls: list[dict] | None = None,
    ) -> None:
        """Add an assistant message."""
        self.messages.append(Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
        ))
        self._trim_messages()
    
    def add_tool_result(
        self,
        tool_call_id: str,
        name: str,
        content: str,
    ) -> None:
        """Add a tool result message."""
        self.messages.append(Message(
            role="tool",
            tool_call_id=tool_call_id,
            name=name,
            content=content,
        ))
        self._trim_messages()
    
    def get_messages(self) -> list[dict]:
        """Get all messages in OpenAI format, including system prompt."""
        result = []

        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})

        for msg in self.messages:
            result.append(msg.to_dict())

        return result

    def validate_and_fix(self) -> bool:
        """Validate message history and fix incomplete tool call sequences.

        Returns:
            True if fixes were made, False if history was valid
        """
        if not self.messages:
            return False

        fixed = False
        i = len(self.messages) - 1

        # Walk backwards to find incomplete tool call sequences
        while i >= 0:
            msg = self.messages[i]

            if msg.role == "assistant" and msg.tool_calls:
                # Check if all tool_calls have corresponding tool responses
                tool_call_ids = {tc["id"] for tc in msg.tool_calls}
                responded_ids = set()

                # Look at subsequent messages for tool responses
                for j in range(i + 1, len(self.messages)):
                    next_msg = self.messages[j]
                    if next_msg.role == "tool" and next_msg.tool_call_id:
                        responded_ids.add(next_msg.tool_call_id)
                    elif next_msg.role in ("user", "assistant"):
                        # Stop at next user/assistant message
                        break

                missing_ids = tool_call_ids - responded_ids
                if missing_ids:
                    # Remove this assistant message and any partial tool responses
                    # that came after it
                    self.messages = self.messages[:i]
                    fixed = True
                    i = len(self.messages) - 1
                    continue

            i -= 1

        return fixed
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
    
    def _trim_messages(self) -> None:
        """Trim messages to max_messages limit."""
        if len(self.messages) > self.max_messages:
            # Keep most recent messages
            self.messages = self.messages[-self.max_messages:]
    
    def to_serializable(self) -> dict:
        """Convert to serializable dict for storage."""
        return {
            "system_prompt": self.system_prompt,
            "messages": [msg.to_dict() for msg in self.messages],
            "max_messages": self.max_messages,
        }
    
    @classmethod
    def from_serializable(cls, data: dict) -> "Context":
        """Restore from serialized dict."""
        ctx = cls(
            system_prompt=data.get("system_prompt", ""),
            max_messages=data.get("max_messages", 500),
        )
        for msg_data in data.get("messages", []):
            ctx.messages.append(Message.from_dict(msg_data))
        return ctx
