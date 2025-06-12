from fastapi import FastAPI
from app.api.v1 import plan_router
from app.api.v2 import embedding_router

app = FastAPI()

# 라우터 등록
app.include_router(plan_router.router, prefix="/api/v1")
app.include_router(embedding_router.router, prefix="/api/v2")