from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from services.db import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(32), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    mode = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
