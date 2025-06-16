from pydantic import BaseModel

class ChatTurnRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str