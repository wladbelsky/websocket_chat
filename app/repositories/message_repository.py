from typing import Sequence

from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message


class MessageRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create(self, chat_id: int, sender_id: int, text: str, load_relationships: bool = False) -> Message:
        async with self.session_factory() as session:
            new_message = Message(
                chat_id=chat_id,
                sender_id=sender_id,
                text=text,
            )
            session.add(new_message)
            await session.commit()
            
            if load_relationships:
                await session.refresh(new_message, ["sender", "chat"])
            else:
                await session.refresh(new_message)
                
            return new_message

    async def get_history(self, chat_id: int, limit: int = 50, offset: int = 0, load_relationships: bool = False) -> Sequence[Message]:
        async with self.session_factory() as session:
            stmt = (
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(asc(Message.timestamp))
                .limit(limit)
                .offset(offset)
            )
            
            if load_relationships:
                stmt = stmt.options(
                    selectinload(Message.sender),
                    selectinload(Message.chat)
                )
                
            result = await session.execute(stmt)
            return result.scalars().all()

    async def mark_as_read(self, message_id: int, load_relationships: bool = False):
        async with self.session_factory() as session:
            stmt = select(Message).where(Message.id == message_id)
            
            if load_relationships:
                stmt = stmt.options(
                    selectinload(Message.sender),
                    selectinload(Message.chat)
                )
                
            result = await session.execute(stmt)
            message = result.scalar_one_or_none()
            
            if message:
                message.is_read = True
                await session.commit()
                
                # Refresh with relationships if requested
                if load_relationships:
                    await session.refresh(message, ["sender", "chat"])
                else:
                    await session.refresh(message)
                    
            return message
