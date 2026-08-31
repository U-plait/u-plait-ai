import time

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
from app.observability import metrics as m

router = APIRouter()


@router.post("/chat")
async def chat_turn(
    request: ChatTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    banword_filter: BanwordFilter = Depends(get_banword_filter)
):
    # 1) 입력 금칙어 검사 (사용자 질문의 어뷰징 감지)
    if banword_filter.contains_banword(request.query):
        m.BANWORD_HIT.labels(source="input").inc()
        m.RECOMMENDATION_FALLBACK.labels(source="banword_input").inc()

        def fake_stream():
            yield "data: 죄송합니다. 알지 못하는 질문입니다.\n\n"
        return StreamingResponse(fake_stream(), media_type="text/event-stream")

    user_info = get_user_info(user_id, db)
    history_pairs = get_recent_chat_pairs(user_id, db)
    m.SESSION_TURNS.observe(len(history_pairs))

    # 2) RAG 검색 계측 (지연 / hits / top-1 score / empty)
    vectorstore = get_vectorstore()
    retrieval_start = time.perf_counter()
    docs_scores = vectorstore.similarity_search_with_score(request.query, k=5)
    m.RETRIEVAL_LATENCY.observe(time.perf_counter() - retrieval_start)
    m.RETRIEVAL_HITS.observe(len(docs_scores))
    if not docs_scores:
        m.RETRIEVAL_EMPTY.inc()
    else:
        # similarity_search_with_score 는 (Document, score) 튜플. pgvector는 distance이므로 낮을수록 유사.
        top1_score = docs_scores[0][1]
        try:
            m.RETRIEVAL_TOP1_SCORE.observe(float(top1_score))
        except (TypeError, ValueError):
            pass

    chain = build_multi_turn_chain()
    context_list = [doc.page_content for doc, _ in docs_scores]

    return StreamingResponse(
        gpt_stream(
            chain,
            request.query,
            history_pairs,
            user_info,
            user_id,
            db,
            context_list,
            banword_filter=banword_filter,
        ),
        media_type="text/event-stream"
    )
