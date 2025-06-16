from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from langchain_core.documents import Document
from app.vector_store import get_vector_store
from app.chat_router import router as chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.post("/vector")
async def save_plan_vector(
    plan_id: int, 
    description: str, 
    db: Session = Depends(get_db)
):
    try:
        # 벡터 저장소 초기화 (컬렉션 자동 생성)
        vector_store = get_vector_store()
        
        # 문서 생성
        doc = Document(
            page_content=description,
            metadata={"plan_id": plan_id}
        )
        
        # 임베딩 저장
        vector_store.add_documents([doc])

        # custom_id 재설정
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