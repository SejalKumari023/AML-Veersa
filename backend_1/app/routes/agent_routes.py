from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.agents.aml_agent import run_aml_agent
from app.database.connection import PostgresDatabase

agent_router = APIRouter()


class AgentRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []
    context: Optional[Dict[str, Any]] = None


class ToolCallLog(BaseModel):
    tool_name: str
    input: Dict[str, Any]
    output: Any


class AgentResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]]
    thought_process: str


class PromptUpdate(BaseModel):
    content: str


@agent_router.post("/agent", response_model=AgentResponse)
async def run_agent(req: AgentRequest):
    """Run the AML monitoring ReAct agent with a natural language message."""
    try:
        result = await run_aml_agent(req.message, req.conversation_history, req.context)
        return AgentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/prompts")
async def get_prompts():
    """List all editable agent prompts."""
    try:
        return await PostgresDatabase.get_all_prompts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.put("/prompts/{name}")
async def update_prompt(name: str, body: PromptUpdate):
    """Update a prompt by name."""
    try:
        result = await PostgresDatabase.upsert_prompt(name, body.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
