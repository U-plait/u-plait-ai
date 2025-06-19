from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/health", response_class=PlainTextResponse)
def health_check():
    return "OK"

@router.get("/test", response_class=PlainTextResponse)
def test_check():
    return "새로운 API 생성"