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
        total_start: float | None = None,
        had_candidates: bool = True,
):
    answer_buffer = ""
    plan_json_buffer = ""
    is_plan_mode = False
    if total_start is None:
        total_start = time.perf_counter()

    # 체인 내부 모델명 안전 추출 실패 시 unknown.
    try:
        model_label = chain.combine_docs_chain.llm_chain.llm.model_name  # type: ignore[attr-defined]
    except Exception:
        model_label = "unknown"

    # --- STAGE 3: llm_generation ---
    llm_start = time.perf_counter()
    first_token_recorded = False
    llm_result = "success"

    try:
        async for chunk in chain.astream({
            "question": request_query,
            "chat_history": history_pairs,
            "user_info": user_info
        }):
            token = chunk.get("answer", "") if isinstance(chunk, dict) else str(chunk)

            if not first_token_recorded and token:
                m.LLM_TTFT.labels(model=model_label).observe(time.perf_counter() - llm_start)
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
            llm_result = "timeout" if "timeout" in reason else "error"
        else:
            m.LLM_ERRORS.labels(provider="openai", model=model_label, reason=reason).inc()
            llm_result = "error"
        # 실패 시에도 지연/토큰 기록 후 상위 SLI 갱신
        elapsed = time.perf_counter() - llm_start
        m.LLM_TOTAL_LATENCY.labels(model=model_label).observe(elapsed)
        m.RECOMMENDATION_DURATION.labels(stage="llm_generation", result="error").observe(elapsed)
        prompt_text = "\n".join(filter(None, [request_query, user_info, *contexts]))
        m.record_llm_usage(
            prompt_text=prompt_text, completion_text=answer_buffer,
            model=model_label, result=llm_result,
        )
        m.RECOMMENDATION_TOTAL.labels(result="fail", stage="llm", failure_type="upstream").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="error").observe(
            time.perf_counter() - total_start
        )
        raise

    # LLM 정상 완료
    elapsed = time.perf_counter() - llm_start
    m.LLM_TOTAL_LATENCY.labels(model=model_label).observe(elapsed)
    m.RECOMMENDATION_DURATION.labels(stage="llm_generation", result="success").observe(elapsed)
    prompt_text = "\n".join(filter(None, [request_query, user_info, *contexts]))
    m.record_llm_usage(
        prompt_text=prompt_text, completion_text=answer_buffer,
        model=model_label, result="success",
    )

    # --- STAGE 4: validation (JSON 파싱 + DB 존재 검증 + 중복 검사) ---
    validation_start = time.perf_counter()

    try:
        cleaned_json = plan_json_buffer.strip().removeprefix("```json").removesuffix("```").strip()
        plan_data = json.loads(cleaned_json)
        parse_ok = True
    except Exception:
        plan_data = {"plan_ids": []}
        parse_ok = False
        m.RECOMMENDATION_FALLBACK.labels(source="parse_failure").inc()

    yield f"data: {json.dumps(plan_data)}\n\n"
    plan_ids = plan_data.get("plan_ids", []) or []
    plans_info: list[dict] = []

    m.RECOMMENDATION_RETURNED.labels(count_bucket=m.bucket_of(len(plan_ids))).inc()

    if plan_ids:
        # 중복 검증
        if len(plan_ids) != len(set(plan_ids)):
            m.RECOMMENDATION_INVALID.labels(reason="duplicate").inc()

        sql = text("""
            SELECT id, plan_name, plan_price, description, dtype
            FROM plan
            WHERE id = ANY(:plan_ids)
        """)
        result = db.execute(sql, {"plan_ids": plan_ids})
        plans_info = [dict(row) for row in result.mappings().all()]

        # DB 존재 검증 (missing_plan)
        found_ids = {row["id"] for row in plans_info}
        missing = [pid for pid in plan_ids if pid not in found_ids]
        for _ in missing:
            m.RECOMMENDATION_INVALID.labels(reason="missing_plan").inc()

        yield f"data: {json.dumps({'plans': plans_info})}\n\n"
        update_user_tags(user_id=user_id, plan_ids=plan_ids, db=db)

    m.RECOMMENDATION_DURATION.labels(
        stage="validation",
        result="success" if parse_ok else "error",
    ).observe(time.perf_counter() - validation_start)

    # 출력 금칙어 검사 (LLM이 금칙어를 뱉는 사고 감지)
    banword_output_hit = False
    if banword_filter is not None and answer_buffer and banword_filter.contains_banword(answer_buffer):
        banword_output_hit = True
        m.BANWORD_HIT.labels(source="output").inc()
        m.RECOMMENDATION_FALLBACK.labels(source="banword_output").inc()

    # --- 최종 SLI 판정 ---
    total_elapsed = time.perf_counter() - total_start
    # 성공 조건: 파싱 성공 AND plan_ids ≥ 1 AND 모두 DB 존재 AND 후보 있었음 AND 출력 금칙어 없음
    all_present = plan_ids and all(pid in {p["id"] for p in plans_info} for pid in plan_ids)
    if not parse_ok:
        m.RECOMMENDATION_TOTAL.labels(result="fail", stage="validation", failure_type="parse").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="error").observe(total_elapsed)
    elif not plan_ids:
        m.RECOMMENDATION_FALLBACK.labels(source="empty_plan_ids").inc()
        m.RECOMMENDATION_TOTAL.labels(result="empty", stage="validation", failure_type="no_candidate").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="empty").observe(total_elapsed)
    elif not all_present:
        m.RECOMMENDATION_TOTAL.labels(result="fail", stage="validation", failure_type="invalid_plan").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="error").observe(total_elapsed)
    elif banword_output_hit:
        m.RECOMMENDATION_TOTAL.labels(result="fallback", stage="response", failure_type="none").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="fallback").observe(total_elapsed)
    elif not had_candidates:
        m.RECOMMENDATION_TOTAL.labels(result="fail", stage="retrieval", failure_type="no_candidate").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="error").observe(total_elapsed)
    else:
        m.RECOMMENDATION_TOTAL.labels(result="success", stage="response", failure_type="none").inc()
        m.RECOMMENDATION_DURATION.labels(stage="total", result="success").observe(total_elapsed)

    db.add(ChatLog(user_id=user_id, log=request_query, is_chatbot=False))
    db.add(ChatLog(user_id=user_id, log=answer_buffer, is_chatbot=True))
    db.commit()
