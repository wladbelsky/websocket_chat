from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.core.containers import Container
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import ChatCreate, ChatResponse
from app.schemas.message import MessageResponse

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse)
@inject
async def create_chat(
        chat_data: ChatCreate,
        current_user: User = Depends(get_current_user),
        chat_repository: ChatRepository = Depends(Provide[Container.chat_repository]),
        user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    """Create a new chat"""
    # Verify all participants exist
    for user_id in chat_data.participant_ids:
        user = await user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    # Verify creator exists if provided
    if chat_data.creator_id:
        creator = await user_repository.get_by_id(chat_data.creator_id)
        if not creator:
            raise HTTPException(status_code=404, detail=f"Creator with ID {chat_data.creator_id} not found")

    try:
        chat = await chat_repository.create(
            name=chat_data.name,
            type_=chat_data.type,
            participant_ids=chat_data.participant_ids,
            creator_id=chat_data.creator_id,
            load_relationships=True
        )
        return ChatResponse(
            id=chat.id,
            name=chat.name,
            type=chat.type,
            participant_ids=[p.user_id for p in chat.participants],
            creator_id=chat.creator_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{chat_id}", response_model=List[MessageResponse])
@inject
async def get_chat_history(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    chat_repository: ChatRepository = Depends(Provide[Container.chat_repository]),
    message_repository: MessageRepository = Depends(Provide[Container.message_repository]),
):
    """
    Get the message history for a specific chat.
    
    Parameters:
    - chat_id: ID of the chat
    - limit: Maximum number of messages to return (default: 50)
    - offset: Number of messages to skip (default: 0)
    
    Returns:
    - List of messages sorted by timestamp (ascending)
    """
    chat = await chat_repository.get_by_id(chat_id, load_relationships=True)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    is_participant = False
    for participant in chat.participants:
        if participant.user_id == current_user.id:
            is_participant = True
            break
    
    if not is_participant:
        raise HTTPException(
            status_code=403, 
            detail="You do not have access to this chat's history"
        )
    
    messages = await message_repository.get_history(
        chat_id=chat_id,
        limit=limit,
        offset=offset,
        load_relationships=True
    )
    
    return messages

