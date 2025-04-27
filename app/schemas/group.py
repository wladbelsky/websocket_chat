from pydantic import BaseModel, Field
from typing import List


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    creator_id: int
    participant_ids: List[int] = Field(..., min_items=2)


class GroupResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    participant_ids: List[int]