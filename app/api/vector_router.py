import time

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from langchain_core.documents import Document
from app.dependencies.vector import get_vectorstore
from app.observability import metrics as m

router = APIRouter(prefix="/vector", tags=["Vector"])


@router.post("")
async def save_plan_vector(
    plan_id: int,
    description: str,
    db: Session = Depends(get_db),
    x_uplait_trigger: str = Header(default="unknown"),
):
    started = time.perf_counter()
    m.INDEXING_DESCRIPTION_CHARS.observe(len(description or ""))
    m.INDEXING_TRIGGER.labels(trigger=x_uplait_trigger or "unknown").inc()

    try:
        db.execute(text("""
            DELETE FROM langchain_pg_embedding
            WHERE cmetadata->>'plan_id' = :plan_id
        """), {"plan_id": str(plan_id)})

        vector_store = get_vectorstore()

        doc = Document(
            page_content=description,
            metadata={"plan_id": plan_id}
        )

        try:
            vector_store.add_documents([doc])
        except Exception as ex:
            m.INDEXING_FAILURES.labels(reason="embedding_error").inc()
            raise ex

        try:
            db.execute(text("""
                UPDATE langchain_pg_embedding
                SET custom_id = 'plan-' || :plan_id
                WHERE cmetadata->>'plan_id' = :plan_id;
            """), {"plan_id": str(plan_id)})
            db.commit()
        except Exception as ex:
            m.INDEXING_FAILURES.labels(reason="db_error").inc()
            raise ex

        m.INDEXING_LATENCY.labels(result="success").observe(time.perf_counter() - started)
        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        m.INDEXING_LATENCY.labels(result="error").observe(time.perf_counter() - started)
        # embedding_error / db_error 는 위에서 잡혔음. 그 외는 unknown으로 카운트.
        raise HTTPException(
            status_code=500,
            detail=f"임베딩 저장 실패: {str(e)}"
        )
