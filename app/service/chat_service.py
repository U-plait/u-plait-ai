from sqlalchemy.orm import Session
from app.models.models import ChatLog

def get_recent_chat_pairs(user_id: int, db: Session) -> list[tuple[str, str]]:
    logs = db.query(ChatLog)\
        .filter(ChatLog.user_id == user_id)\
        .order_by(ChatLog.id.desc())\
        .limit(6).all()
    logs.reverse()
    history_pairs = []
    i = 0
    while i < len(logs) - 1:
        if not logs[i].is_chatbot and logs[i+1].is_chatbot:
            history_pairs.append((logs[i].log, logs[i+1].log))
            i += 2
        else:
            i += 1
    return history_pairs