from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import ChatTurnRequest
from app.core.jwt_auth import get_current_user_id
from app.core.database import get_db
from app.service.rag_service import build_multi_turn_chain
from fastapi.responses import StreamingResponse
from app.dependencies.vector import get_vectorstore
from app.service.user_service import get_user_info
from app.service.chat_service import get_recent_chat_pairs
from app.service.stream_service import gpt_stream
from app.dependencies.banword import get_banword_filter
from app.utils.banword_filter import BanwordFilter

router = APIRouter()


@router.post("/chat")
async def chat_turn(
    request: ChatTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    banword_filter: BanwordFilter = Depends(get_banword_filter)
):
    if banword_filter.contains_banword(request.query):
        def fake_stream():
            yield "data: 죄송합니다. 알지 못하는 질문입니다.\n\n"
        return StreamingResponse(fake_stream(), media_type="text/event-stream")

    user_info = get_user_info(user_id, db)
    history_pairs = get_recent_chat_pairs(user_id, db)

    vectorstore = get_vectorstore()  
    docs_scores = vectorstore.similarity_search_with_score(request.query, k=5)

    chain = build_multi_turn_chain()
    context_list = [doc.page_content for doc, _ in docs_scores]
    
    return StreamingResponse(
        gpt_stream(chain, request.query, history_pairs, user_info, user_id, db, context_list),
        media_type="text/event-stream"
    )