from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Literal


class MessageType(str, Enum):
    """Types of websocket messages"""
    MESSAGE = "message"
    READ_STATUS = "read_status"


class BaseWebSocketMessage(BaseModel):
    """Base model for all websocket messages"""
    type: MessageType


class ChatMessageIn(BaseWebSocketMessage):
    """Message received from a client"""
    type: Literal[MessageType.MESSAGE] = MessageType.MESSAGE
    content: str


class ChatMessageOut(BaseWebSocketMessage):
    """Message sent to clients"""
    type: Literal[MessageType.MESSAGE] = MessageType.MESSAGE
    id: int
    sender_id: int
    content: str
    timestamp: datetime
    is_read: bool


class ReadStatusIn(BaseWebSocketMessage):
    """Read status notification from a client"""
    type: Literal[MessageType.READ_STATUS] = MessageType.READ_STATUS
    message_id: int


class ReadStatusOut(BaseWebSocketMessage):
    """Read status notification to clients"""
    type: Literal[MessageType.READ_STATUS] = MessageType.READ_STATUS
    message_id: int
    reader_id: int
    timestamp: datetime
