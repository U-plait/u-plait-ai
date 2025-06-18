from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat_router import router as chat_router
from app.api.vector_router import router as vector_router
from app.api.health_router import router as health_router
import logging

app = FastAPI()

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
