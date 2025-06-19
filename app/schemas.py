# schemas.pt
from pydantic import BaseModel

class ChatTurnRequest(BaseModel):
    query: str
