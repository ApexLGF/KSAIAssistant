"""REST API routes."""

from fastapi import APIRouter, HTTPException

from web.schemas import HealthResponse, ToolInfo, SkillInfo

router = APIRouter(prefix="/api")

# Agent instance will be set by main.py
_agent = None


def set_agent(agent):
    """Set the agent instance for routes."""
    global _agent
    _agent = agent


def get_agent():
    """Get the agent instance."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return _agent


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    agent = get_agent()
    return HealthResponse(
        status="ok",
        tools_count=len(agent.registry),
        skills_count=len(agent.skill_loader.list_skills()),
    )


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools():
    """List available tools."""
    agent = get_agent()
    return [
        ToolInfo(name=t["name"], description=t["description"])
        for t in agent.list_tools()
    ]


@router.get("/skills", response_model=list[SkillInfo])
async def list_skills():
    """List loaded skills."""
    agent = get_agent()
    return [
        SkillInfo(name=s["name"], description=s["description"], type=s["type"])
        for s in agent.list_skills()
    ]


@router.delete("/history")
async def clear_history():
    """Clear conversation history."""
    agent = get_agent()
    agent.clear_history()
    return {"status": "ok", "message": "History cleared"}
