# app/api/v1/plan_router.py
from fastapi import APIRouter
from app.schemas.plan import PlanRequest

router = APIRouter()

@router.get("/query/")
def get_answer(query: str):
    return "MAIN API"

@router.post("/embedding")
async def embed_plan(request: PlanRequest):
    print(f"[서버 수신] title: {request.title}, description: {request.description}")
    return {"message": "요금제 정상 수신"}