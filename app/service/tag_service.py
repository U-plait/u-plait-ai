from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

def update_user_tags(user_id: int, plan_ids: list[int], db: Session):
    tag_query = text("""
        SELECT DISTINCT pt.tag_id
        FROM plan_tag pt
        WHERE pt.plan_id = ANY(:plan_ids)
    """)
    result = db.execute(tag_query, {"plan_ids": plan_ids})
    tag_ids = [row[0] for row in result.fetchall()]

    now = datetime.utcnow()

    for tag_id in tag_ids:
        check_query = text("""
            SELECT tag_count FROM user_tag
            WHERE user_id = :user_id AND tag_id = :tag_id
        """)
        res = db.execute(check_query, {"user_id": user_id, "tag_id": tag_id})
        existing = res.fetchone()

        if existing:
            db.execute(text("""
                UPDATE user_tag 
                SET tag_count = tag_count + 1, updated_at = :now
                WHERE user_id = :user_id AND tag_id = :tag_id
            """), {"user_id": user_id, "tag_id": tag_id, "now": now})
        else:
            db.execute(text("""
                INSERT INTO user_tag (user_id, tag_id, tag_count, created_at, updated_at)
                VALUES (:user_id, :tag_id, 1, :now, :now)
            """), {"user_id": user_id, "tag_id": tag_id, "now": now})

    db.commit()
