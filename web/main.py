"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from agent.config import load_config
from agent.core.agent import Agent
from web.routes import router, set_agent
from web.websocket import handle_chat_websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
_agent: Agent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global _agent

    # Startup: Initialize agent
    logger.info("Initializing agent...")
    config = load_config()
    _agent = Agent(config)
    await _agent.initialize()
    set_agent(_agent)
    logger.info("Agent initialized successfully")

    yield

    # Shutdown: Cleanup
    logger.info("Shutting down agent...")
    if _agent:
        await _agent.shutdown()
    logger.info("Agent shutdown complete")


app = FastAPI(
    title="TestAIAgent API",
    description="Web API for TestAIAgent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for chat."""
    await handle_chat_websocket(websocket, _agent)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
