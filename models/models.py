from pydantic import BaseModel
from typing import List, Optional
from helpers.db import Base
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, TIMESTAMP, Integer, Text, JSON, func
from sqlalchemy.dialects import postgresql


BigIntegerType = BigInteger()
BigIntegerType = BigIntegerType.with_variant(postgresql.BIGINT(), "postgresql")


class ChatHistory(BaseModel):
    org_id: int
    time_stamp: Optional[float]  # Example: You can store some identifier or timestamp for the history
    chat: List



class Organization(Base):
    __tablename__ = "organizations"

    id = Column(BigIntegerType, primary_key=True, autoincrement=True)
    name = Column(String(255))
    embedding_model = Column(String)
    pine_index = Column(String)
    es_index = Column(String)

    def __init__(self, name, embedding_model=None, pine_index=None, es_index=None):
        self.name = name
        self.embedding_model = embedding_model
        self.pine_index = pine_index
        self.es_index = es_index


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "embedding_model": self.embedding_model,
            "pine_index": self.pine_index,
            "es_index": self.es_index,
        }
    

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False)
    org_id = Column(BigInteger, nullable=False)
    history = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    def __repr__(self):
        return f"<Chat(id={self.id}, user_id={self.user_id}, org_id={self.org_id})>"