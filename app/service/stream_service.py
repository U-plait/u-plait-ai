import asyncio
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import ChatLog
from app.service.tag_service import update_user_tags
from app.utils.eval_logger import save_eval_sample

async def gpt_stream(
        chain,
        request_query: str,
        history_pairs: list,
        user_info: str,
        user_id: int,
        db: Session,
        contexts: list[str]
):
    answer_buffer = ""
    plan_json_buffer = ""
    is_plan_mode = False

    async for chunk in chain.astream({
        "question": request_query,
        "chat_history": history_pairs,
        "user_info": user_info
    }):
        token = chunk.get("answer", "") if isinstance(chunk, dict) else str(chunk)

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

    try:
        cleaned_json = plan_json_buffer.strip().removeprefix("```json").removesuffix("```").strip()
        plan_data = json.loads(cleaned_json)
    except Exception:
        plan_data = {"plan_ids": []}

    yield f"data: {json.dumps(plan_data)}\n\n"
    plan_ids = plan_data.get("plan_ids", [])
    plans_info = []

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

    db.add(ChatLog(user_id=user_id, log=request_query, is_chatbot=False))
    db.add(ChatLog(user_id=user_id, log=answer_buffer, is_chatbot=True))
    db.commit()