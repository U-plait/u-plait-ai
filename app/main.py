from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.chat_router import router as chat_router
from app.api.vector_router import router as vector_router
from app.api.health_router import router as health_router
from app.dependencies.vector import init_vectorstore
from app.dependencies.llm import init_llm
from app import observability  # noqa: F401 — 지표 모듈 로드로 Prometheus 레지스트리 초기화
from dotenv import load_dotenv
import logging
import os

app = FastAPI()

load_dotenv(override=True)

print("[DEBUG] EMBEDDING_SOURCE =", os.getenv("EMBEDDING_SOURCE"))
print("[DEBUG] DATABASE_URL =", os.getenv("DATABASE_URL"))

@app.on_event("startup")
def startup_event():
    print("[STARTUP] Initializing VectorStore & LLM...")
    init_vectorstore()
    init_llm()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "https://uplait.site",
        "http://localhost:8000", "https://cb.uplait.site"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Observability ---
# HTTP 기본 지표(http_requests_total, http_request_duration_seconds 등) + custom 지표를
# 한 엔드포인트에서 노출. /metrics 자체는 스크래핑 대상에서 제외.
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(chat_router)
app.include_router(vector_router)
app.include_router(health_router)

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
