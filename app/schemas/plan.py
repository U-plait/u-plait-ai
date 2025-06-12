from pydantic import BaseModel

class PlanRequest(BaseModel):
    title: str
    description: str
