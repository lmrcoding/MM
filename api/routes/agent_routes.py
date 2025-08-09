from fastapi import APIRouter
from models.schemas import AgentInput
from logic.agent_brain import agent_brain

router = APIRouter(prefix="/agent", tags=["Agent Logic"])

@router.post("/run")
def run_agent(data: AgentInput):
    return agent_brain(data.model_dump())

@router.get("/status")
def agent_status():
    return {"status": "Agent system is ready."}
