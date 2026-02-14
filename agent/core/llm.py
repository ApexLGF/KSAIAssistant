"""OpenAI LLM client for TestAIAgent."""

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import AsyncIterator, Awaitable, Callable

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from agent.config import OpenAIConfig, DeepSeekConfig


@dataclass
class StreamResult:
    """Result of a streaming chat completion."""
    
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)


class LLMClient:
    """OpenAI API client wrapper with DeepSeek fallback."""

    def __init__(self, openai_config: OpenAIConfig, deepseek_config: DeepSeekConfig | None = None):
        """Initialize the LLM client.

        Args:
            openai_config: OpenAI configuration
            deepseek_config: Optional DeepSeek configuration for fallback
        """
        self.openai_config = openai_config
        self.deepseek_config = deepseek_config

        self.openai_client = AsyncOpenAI(
            api_key=openai_config.api_key,
            base_url=openai_config.base_url,
        )

        self.deepseek_client = None
        if deepseek_config and deepseek_config.api_key:
            self.deepseek_client = AsyncOpenAI(
                api_key=deepseek_config.api_key,
                base_url=deepseek_config.base_url,
            )
    
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        """Send a chat completion request (non-streaming).
        
        Args:
            messages: List of message dicts (role, content)
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy ("auto", "none", "required")
            
        Returns:
            The response message dict
        """
        kwargs = {
            "model": self.config.model,
            "messages": messages,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message
    
    async def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        on_content: Callable[[str], None] | Callable[[str], Awaitable[None]] | None = None,
    ) -> StreamResult:
        """Stream a chat completion response with fallback support.

        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            on_content: Callback for each content chunk (sync or async)

        Returns:
            StreamResult with full content and any tool calls
        """
        # Try OpenAI first
        try:
            return await self._chat_stream_with_client(
                self.openai_client,
                self.openai_config.model,
                messages,
                tools,
                on_content,
            )
        except (APIConnectionError, APIError, RateLimitError, Exception) as e:
            # If OpenAI fails and DeepSeek is configured, try DeepSeek
            if self.deepseek_client:
                print(f"[LLM] OpenAI failed ({type(e).__name__}: {e}), falling back to DeepSeek...")
                try:
                    return await self._chat_stream_with_client(
                        self.deepseek_client,
                        self.deepseek_config.model,
                        messages,
                        tools,
                        on_content,
                    )
                except Exception as fallback_error:
                    print(f"[LLM] DeepSeek also failed: {fallback_error}")
                    raise
            else:
                # No fallback available, re-raise
                raise

    async def _chat_stream_with_client(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        on_content: Callable[[str], None] | Callable[[str], Awaitable[None]] | None = None,
    ) -> StreamResult:
        """Internal method to stream chat with a specific client.

        Args:
            client: OpenAI client instance
            model: Model name
            messages: List of message dicts
            tools: Optional list of tool definitions
            on_content: Callback for each content chunk (sync or async)

        Returns:
            StreamResult with full content and any tool calls
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = tools

        result = StreamResult()
        tool_calls_data: dict[int, dict] = {}  # index -> {id, name, arguments}

        stream = await client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle content
            if delta.content:
                result.content += delta.content
                if on_content:
                    # Support both sync and async callbacks
                    if asyncio.iscoroutinefunction(on_content):
                        await on_content(delta.content)
                    else:
                        on_content(delta.content)

            # Handle tool calls
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index

                    if idx not in tool_calls_data:
                        tool_calls_data[idx] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }

                    tc = tool_calls_data[idx]

                    if tc_delta.id:
                        tc["id"] = tc_delta.id

                    if tc_delta.function:
                        if tc_delta.function.name:
                            tc["function"]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tc["function"]["arguments"] += tc_delta.function.arguments

        # Convert tool_calls_data to list
        if tool_calls_data:
            result.tool_calls = [tool_calls_data[i] for i in sorted(tool_calls_data.keys())]

        return result
