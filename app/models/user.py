from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    messages_sent = relationship("Message", back_populates="sender", cascade="all, delete-orphan")
    chats = relationship("ChatParticipant", back_populates="user", cascade="all, delete-orphan")
    chats_created = relationship("Chat", foreign_keys="Chat.creator_id", back_populates="creator")
