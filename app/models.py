from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func

Base = declarative_base()

class PlanVector(Base):
    __tablename__ = 'plan_vector'

    id = Column(BigInteger, primary_key=True)
    plan_id = Column(BigInteger, nullable=False)
    description = Column(Text)
    embedding = Column(Vector(1536))
    
class ChatLog(Base):
    __tablename__= 'chat_log'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    log = Column(Text, nullable=False)
    sequence = Column(BigInteger, nullable=False)
    is_chatbot = Column(Boolean, nullable=False)    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())