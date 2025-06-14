from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PlanVector
from app.embedding import get_embedding
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
async def save_plan_vector(plan_id: int, description: str, db: Session = Depends(get_db)):
    try:
        embedding = get_embedding(description)

        new_vector_plan = PlanVector(
            plan_id=plan_id,
            description=description,
            embedding=embedding
        )

        db.add(new_vector_plan)
        db.commit()
        db.refresh(new_vector_plan)
    
        return {"status": "success", "vector_id": new_vector_plan.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

