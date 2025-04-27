from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.chat import ChatType


class ChatCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: ChatType
    participant_ids: List[int] = Field(..., min_items=2)
    creator_id: Optional[int] = None


class ChatResponse(BaseModel):
    id: int
    name: str
    type: ChatType
    participant_ids: List[int]
    creator_id: Optional[int] = None
