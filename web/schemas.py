"""Pydantic models for API requests and responses."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    tools_count: int
    skills_count: int


class ToolInfo(BaseModel):
    """Tool information."""

    name: str
    description: str


class SkillInfo(BaseModel):
    """Skill information."""

    name: str
    description: str
    type: str


class WSMessage(BaseModel):
    """WebSocket message from client."""

    type: str
    content: str = ""


class WSContentResponse(BaseModel):
    """WebSocket content chunk response."""

    type: str = "content"
    content: str


class WSToolCallResponse(BaseModel):
    """WebSocket tool call response."""

    type: str = "tool_call"
    name: str
    args: dict
    status: str  # "started" or "completed"
    result: str = ""


class WSDoneResponse(BaseModel):
    """WebSocket done response."""

    type: str = "done"
    full_content: str


class WSErrorResponse(BaseModel):
    """WebSocket error response."""

    type: str = "error"
    message: str
