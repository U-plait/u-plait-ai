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

RETRIEVAL_K = 5


@router.post("/chat")
async def chat_turn(
    request: ChatTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    banword_filter: BanwordFilter = Depends(get_banword_filter)
):
    total_start = time.perf_counter()

    # --- STAGE 1: input_processing (banword + user_info + history) ---
    input_start = time.perf_counter()
    if banword_filter.contains_banword(request.query):
        m.BANWORD_HIT.labels(source="input").inc()
        m.RECOMMENDATION_FALLBACK.labels(source="banword_input").inc()
        m.RECOMMENDATION_TOTAL.labels(result="fallback", stage="validation", failure_type="none").inc()
        m.RECOMMENDATION_DURATION.labels(stage="input_processing", result="fallback").observe(
            time.perf_counter() - input_start
        )
        m.RECOMMENDATION_DURATION.labels(stage="total", result="fallback").observe(
            time.perf_counter() - total_start
        )

        def fake_stream():
            yield "data: 죄송합니다. 알지 못하는 질문입니다.\n\n"
        return StreamingResponse(fake_stream(), media_type="text/event-stream")

    user_info = get_user_info(user_id, db)
    history_pairs = get_recent_chat_pairs(user_id, db)
    m.SESSION_TURNS.observe(len(history_pairs))
    m.RECOMMENDATION_DURATION.labels(stage="input_processing", result="success").observe(
        time.perf_counter() - input_start
    )

    # --- STAGE 2: vector_search (pgvector similarity_search) ---
    vectorstore = get_vectorstore()
    retrieval_start = time.perf_counter()
    try:
        docs_scores = vectorstore.similarity_search_with_score(request.query, k=RETRIEVAL_K)
    except Exception:
        elapsed = time.perf_counter() - retrieval_start
        m.RETRIEVAL_LATENCY.observe(elapsed)
        m.RETRIEVAL_TOTAL.labels(result="error").inc()
        m.RECOMMENDATION_DURATION.labels(stage="vector_search", result="error").observe(elapsed)
        m.RECOMMENDATION_TOTAL.labels(result="fail", stage="retrieval", failure_type="upstream").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="error").observe(
            time.perf_counter() - total_start
        )
        raise
    retrieval_elapsed = time.perf_counter() - retrieval_start
    m.RETRIEVAL_LATENCY.observe(retrieval_elapsed)
    m.RECOMMENDATION_DURATION.labels(stage="vector_search", result="success").observe(retrieval_elapsed)
    m.RETRIEVAL_HITS.observe(len(docs_scores))
    m.RETRIEVAL_TOTAL.labels(result=m.classify_retrieval(len(docs_scores), RETRIEVAL_K)).inc()

    if not docs_scores:
        # 검색 결과 0건 → 추천 무의미. 하지만 LLM은 여전히 폴백 응답을 생성 가능.
        # 이 지점을 SLI 상 fail 로 잡음 (no_candidate).
        m.RECOMMENDATION_TOTAL.labels(result="fail", stage="retrieval", failure_type="no_candidate").inc()
    else:
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
            total_start=total_start,
            had_candidates=bool(docs_scores),
        ),
        media_type="text/event-stream"
    )
