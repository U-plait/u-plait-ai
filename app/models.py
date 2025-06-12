from sqlalchemy import Column, BigInteger, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

class PlanVector(Base):
    __tablename__ = 'plan_vector'

    id = Column(BigInteger, primary_key=True)
    plan_id = Column(BigInteger, nullable=False)
    description = Column(Text)
    embedding = Column(Vector(768))
    