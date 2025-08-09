from pydantic import BaseModel

class AgentInput(BaseModel):
    name: str
    query: str
