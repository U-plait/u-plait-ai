from app.core.embedding import get_embedding

@router.post("/embedding")
async def embed_plan(request: PlanRequest):
    full_text = f"{request.title}. {request.description}"
    vector = get_embedding(full_text)
    print("[임베딩] 벡터 길이:", len(vector))
    return {"message": "임베딩 완료", "vector_dim": len(vector)}
