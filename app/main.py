# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat_router import router as chat_router
from app.api.vector_router import router as vector_router
from app.api.health_router import router as health_router
from app.dependencies.vector import init_vectorstore
from app.dependencies.llm import init_llm
import logging

app = FastAPI()

import os
from dotenv import load_dotenv

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

app.include_router(chat_router)
app.include_router(vector_router)
app.include_router(health_router)

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)