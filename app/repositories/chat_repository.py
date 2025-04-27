from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Chat, ChatType
from app.models.chat_participant import ChatParticipant


class ChatRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create(self, name: str, type_: ChatType, participant_ids: list[int], creator_id: int = None, load_relationships: bool = False) -> Chat:
        """Create a new chat with participants

        Args:
            name: The name of the chat
            type_: The type of chat (personal or group)
            participant_ids: List of all participant user IDs
            creator_id: The ID of the user who created the chat (required for group chats)
            load_relationships: Whether to load related entities

        Raises:
            ValueError: If there are fewer than 2 participants
            ValueError: If creator_id is not provided for a group chat
        """
        if len(participant_ids) < 2:
            raise ValueError("Chat must have at least 2 participants")

        if type_ == ChatType.group and creator_id is None:
            raise ValueError("Group chat must have a creator")

        unique_participant_ids = list(set(participant_ids))

        # Ensure creator is in the participants list for group chats
        if type_ == ChatType.group and creator_id not in unique_participant_ids:
            unique_participant_ids.append(creator_id)

        async with self.session_factory() as session:
            new_chat = Chat(name=name, type=type_, creator_id=creator_id)
            session.add(new_chat)
            await session.flush()

            for user_id in unique_participant_ids:
                participant = ChatParticipant(chat_id=new_chat.id, user_id=user_id)
                session.add(participant)

            await session.commit()
            
            if load_relationships:
                await session.refresh(new_chat, ["participants", "messages", "creator"])
            else:
                await session.refresh(new_chat)
                
            return new_chat

    async def get_by_id(self, chat_id: int, load_relationships: bool = False) -> Chat | None:
        async with self.session_factory() as session:
            stmt = select(Chat).where(Chat.id == chat_id)
            
            if load_relationships:
                stmt = stmt.options(
                    selectinload(Chat.participants),
                    selectinload(Chat.messages),
                    selectinload(Chat.creator)
                )
                
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_chats(self, user_id: int, limit: int = 100, offset: int = 0, load_relationships: bool = False) -> Sequence[Chat]:
        """List chats where the specified user is a participant"""
        async with self.session_factory() as session:
            stmt = (
                select(Chat)
                .join(ChatParticipant, Chat.id == ChatParticipant.chat_id)
                .where(ChatParticipant.user_id == user_id)
                .limit(limit)
                .offset(offset)
            )
            
            if load_relationships:
                stmt = stmt.options(
                    selectinload(Chat.participants),
                    selectinload(Chat.messages),
                    selectinload(Chat.creator)
                )
                
            result = await session.execute(stmt)
            return result.scalars().all()
