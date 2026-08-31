import asyncio
import json
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import ChatLog
from app.service.tag_service import update_user_tags
from app.utils.eval_logger import save_eval_sample
from app.utils.banword_filter import BanwordFilter
from app.observability import metrics as m


async def gpt_stream(
        chain,
        request_query: str,
        history_pairs: list,
        user_info: str,
        user_id: int,
        db: Session,
        contexts: list[str],
        banword_filter: BanwordFilter | None = None,
):
    answer_buffer = ""
    plan_json_buffer = ""
    is_plan_mode = False

    # LLM 호출 계측: TTFT + 총 지연.
    call_start = time.perf_counter()
    first_token_recorded = False
    # 체인 내부 모델 이름 안전 추출 실패 시 unknown 사용.
    try:
        model_label = chain.combine_docs_chain.llm_chain.llm.model_name  # type: ignore[attr-defined]
    except Exception:
        model_label = "unknown"

    try:
        async for chunk in chain.astream({
            "question": request_query,
            "chat_history": history_pairs,
            "user_info": user_info
        }):
            token = chunk.get("answer", "") if isinstance(chunk, dict) else str(chunk)

            if not first_token_recorded and token:
                m.LLM_TTFT.labels(model=model_label).observe(time.perf_counter() - call_start)
                first_token_recorded = True

            if "[END_OF_MESSAGE]" in token:
                is_plan_mode = True
                parts = token.split("[END_OF_MESSAGE]")

                answer_buffer += parts[0]
                for char in parts[0]:
                    yield f"data: {char}\n\n"
                    await asyncio.sleep(0.01)

                yield f"data: [END_OF_MESSAGE]\n\n"

                if len(parts) > 1:
                    plan_json_buffer += parts[1]
                    answer_buffer += "[END_OF_MESSAGE]" + parts[1]
                continue

            if not is_plan_mode:
                answer_buffer += token
                for char in token:
                    yield f"data: {char}\n\n"
                    await asyncio.sleep(0.01)
            else:
                plan_json_buffer += token
    except Exception as ex:
        reason = type(ex).__name__.lower()
        if "ratelimit" in reason:
            m.LLM_RATE_LIMIT.labels(provider="openai", model=model_label).inc()
        else:
            m.LLM_ERRORS.labels(provider="openai", model=model_label, reason=reason).inc()
        raise
    finally:
        m.LLM_TOTAL_LATENCY.labels(model=model_label).observe(time.perf_counter() - call_start)
        # 토큰 사용량 기록 (prompt = 질문 + user_info + 상위 context 합침)
        prompt_text = "\n".join(filter(None, [request_query, user_info, *contexts]))
        m.record_llm_usage(prompt_text=prompt_text, completion_text=answer_buffer, model=model_label)

    # 응답 파싱
    try:
        cleaned_json = plan_json_buffer.strip().removeprefix("```json").removesuffix("```").strip()
        plan_data = json.loads(cleaned_json)
        parse_ok = True
    except Exception:
        plan_data = {"plan_ids": []}
        parse_ok = False
        m.RECOMMENDATION_FALLBACK.labels(source="parse_failure").inc()

    yield f"data: {json.dumps(plan_data)}\n\n"
    plan_ids = plan_data.get("plan_ids", [])
    plans_info = []

    # 추천 결과 지표
    m.RECOMMENDATION_RETURNED.labels(count_bucket=m.bucket_of(len(plan_ids))).inc()
    if parse_ok and not plan_ids:
        m.RECOMMENDATION_FALLBACK.labels(source="empty_plan_ids").inc()

    if plan_ids:
        sql = text("""
            SELECT id, plan_name, plan_price, description, dtype
            FROM plan
            WHERE id = ANY(:plan_ids)
        """)
        result = db.execute(sql, {"plan_ids": plan_ids})
        plans_info = [dict(row) for row in result.mappings().all()]
        yield f"data: {json.dumps({'plans': plans_info})}\n\n"

    if plan_data.get("plan_ids"):
        update_user_tags(user_id=user_id, plan_ids=plan_data["plan_ids"], db=db)

    # 출력 금칙어 검사 (LLM이 금칙어를 뱉는 사고 감지)
    if banword_filter is not None and answer_buffer and banword_filter.contains_banword(answer_buffer):
        m.BANWORD_HIT.labels(source="output").inc()
        m.RECOMMENDATION_FALLBACK.labels(source="banword_output").inc()

    db.add(ChatLog(user_id=user_id, log=request_query, is_chatbot=False))
    db.add(ChatLog(user_id=user_id, log=answer_buffer, is_chatbot=True))
    db.commit()
