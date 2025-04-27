from datetime import datetime
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Model for message response data"""
    id: int
    sender_id: int
    chat_id: int
    text: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True
