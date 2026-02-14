"""WebSocket handler for chat."""

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from web.schemas import (
    WSContentResponse,
    WSToolCallResponse,
    WSDoneResponse,
    WSErrorResponse,
)

logger = logging.getLogger(__name__)

# Welcome message flag per connection
_welcome_sent = {}


async def handle_chat_websocket(websocket: WebSocket, agent):
    """Handle WebSocket chat connection.

    Protocol:
    - Client sends: {"type": "message", "content": "user input"}
    - Server sends: {"type": "content", "content": "chunk"}
    - Server sends: {"type": "tool_call", "name": "...", "args": {...}, "status": "started|completed", "result": "..."}
    - Server sends: {"type": "done", "full_content": "complete response"}
    - Server sends: {"type": "error", "message": "error message"}
    """
    await websocket.accept()
    connection_id = id(websocket)

    # Send welcome message on first connection
    if connection_id not in _welcome_sent:
        _welcome_sent[connection_id] = True
        welcome_msg = "Hello! I'm the sales assistant for Everlasting Cabinetry. How can I help you today?"
        await websocket.send_json(
            WSContentResponse(content=welcome_msg).model_dump()
        )
        await websocket.send_json(
            WSDoneResponse(full_content=welcome_msg).model_dump()
        )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json(
                    WSErrorResponse(message="Invalid JSON").model_dump()
                )
                continue

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if message.get("type") != "message":
                await websocket.send_json(
                    WSErrorResponse(message="Unknown message type").model_dump()
                )
                continue

            user_input = message.get("content", "").strip()
            if not user_input:
                await websocket.send_json(
                    WSErrorResponse(message="Empty message").model_dump()
                )
                continue

            # Handle special commands
            if user_input.startswith("/"):
                result = await handle_command(user_input, agent)
                if result is not None:
                    await websocket.send_json(
                        WSDoneResponse(full_content=result).model_dump()
                    )
                    continue

            # Process the message with streaming
            try:
                full_content = await process_chat(websocket, agent, user_input)
                await websocket.send_json(
                    WSDoneResponse(full_content=full_content).model_dump()
                )
            except Exception as e:
                logger.exception("Error processing chat")
                await websocket.send_json(
                    WSErrorResponse(message=str(e)).model_dump()
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        # Clean up welcome flag
        if connection_id in _welcome_sent:
            del _welcome_sent[connection_id]


async def handle_command(user_input: str, agent) -> str | None:
    """Handle special slash commands.

    Returns:
        Response string if command was handled, None otherwise
    """
    cmd = user_input.lower().split()[0]

    if cmd == "/tools":
        tools = agent.list_tools()
        if not tools:
            return "No tools available."
        lines = ["**Available Tools:**\n"]
        for tool in tools:
            lines.append(f"- **{tool['name']}**: {tool['description']}")
        return "\n".join(lines)

    elif cmd == "/skills":
        skills = agent.list_skills()
        if not skills:
            return "No skills loaded."
        lines = ["**Loaded Skills:**\n"]
        for skill in skills:
            type_badge = f"[{skill['type']}]"
            lines.append(f"- **{skill['name']}** {type_badge}: {skill['description']}")
        return "\n".join(lines)

    elif cmd == "/clear":
        agent.clear_history()
        return "Conversation history cleared."

    elif cmd == "/help":
        return """**Available Commands:**

- `/tools` - List available tools
- `/skills` - List loaded skills
- `/clear` - Clear conversation history
- `/help` - Show this help message"""

    # Not a recognized command, let LLM handle it
    return None


async def process_chat(websocket: WebSocket, agent, user_input: str) -> str:
    """Process chat message and stream responses."""

    async def on_content(chunk: str):
        """Send content chunk to client."""
        await websocket.send_json(WSContentResponse(content=chunk).model_dump())

    async def on_tool_call(name: str, args: dict, status: str, result: str):
        """Send tool call event to client."""
        await websocket.send_json(
            WSToolCallResponse(
                name=name, args=args, status=status, result=result
            ).model_dump()
        )

    # Run chat with callbacks
    response = await agent.chat_stream(
        user_input=user_input,
        on_content=on_content,
        on_tool_call=on_tool_call,
    )

    return response
