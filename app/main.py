from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import init_db
from app.models import PlanVector
from app.embedding import get_embedding

app = FastAPI()

@app.post("/vector")
def save_plan_vector(plan_id: int, description: str, db: Session = Depends(init_db)):
    embedding = get_embedding(description)

    new_vector_plan = PlanVector(
        plan_id=plan_id,
        description=description,
        embedding=embedding
    )

    db.add(new_vector_plan)
    db.commit()
    db.refresh(new_vector_plan)

    return
