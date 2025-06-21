# user_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_user_info(user_id: int, db: Session) -> str:
    sql = text("""
        SELECT u.name, u.age, u.gender,
               COALESCE(string_agg(t.name, ', ' ORDER BY ut.tag_count DESC), '') AS top_tags
        FROM users u
        LEFT JOIN user_tag ut ON u.id = ut.user_id
        LEFT JOIN tag t ON ut.tag_id = t.id
        WHERE u.id = :user_id
        GROUP BY u.id, u.name, u.age, u.gender
    """)
    result = db.execute(sql, {"user_id": user_id}).fetchone()

    if result:
        user_name, user_age, user_gender, top_tags_str = result
        top_tags = top_tags_str.split(', ')[:2]
        return f"사용자 이름: {user_name}, 나이: {user_age}, 성별: {user_gender}" + \
               (f", 주요 관심 태그: {', '.join(top_tags)}" if top_tags else "")
    return "사용자 정보 없음"