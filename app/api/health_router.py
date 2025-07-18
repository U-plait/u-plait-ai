from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/health", response_class=PlainTextResponse)
def health_check():
    return "OK"
