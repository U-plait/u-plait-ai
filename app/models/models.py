from sqlalchemy import Column, BigInteger, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()
    
class ChatLog(Base):
    __tablename__= 'chat_log'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    log = Column(Text, nullable=False)
    is_chatbot = Column(Boolean, nullable=False)    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())