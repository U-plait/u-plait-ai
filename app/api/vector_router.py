# vector_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from langchain_core.documents import Document
from app.dependencies.vector import get_vectorstore

router = APIRouter(prefix="/vector", tags=["Vector"])

@router.post("")
async def save_plan_vector(
    plan_id: int, 
    description: str, 
    db: Session = Depends(get_db)
):
    try:
        vector_store = get_vectorstore()
        
        doc = Document(
            page_content=description,
            metadata={"plan_id": plan_id}
        )
        
        vector_store.add_documents([doc])

        db.execute(text("""
            UPDATE langchain_pg_embedding
            SET custom_id = 'plan-' || :plan_id
            WHERE cmetadata->>'plan_id' = :plan_id;
        """), {"plan_id": str(plan_id)})

        db.commit()
        return {"status": "success"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"임베딩 저장 실패: {str(e)}"
        )
