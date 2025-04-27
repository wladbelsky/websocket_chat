from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_by_email(self, email: str, load_relationships: bool = False) -> User | None:
        async with self.session_factory() as session:
            stmt = select(User).where(User.email == email)
            
            if load_relationships:
                stmt = stmt.options(
                    selectinload(User.participations),
                    selectinload(User.chats),
                    selectinload(User.messages)
                )
                
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create(self, name: str, email: str, hashed_password: str, load_relationships: bool = False) -> User:
        async with self.session_factory() as session:
            user = User(name=name, email=email, password=hashed_password)
            session.add(user)
            await session.commit()
            
            # Optionally load relationships after creation
            if load_relationships:
                await session.refresh(user, ["participations", "chats", "messages"])
            else:
                await session.refresh(user)
                
            return user

    async def get_by_id(self, user_id: int, load_relationships: bool = False) -> User | None:
        async with self.session_factory() as session:
            stmt = select(User).where(User.id == user_id)
            
            if load_relationships:
                stmt = stmt.options(
                    selectinload(User.messages_sent),
                    selectinload(User.chats),
                    selectinload(User.chats_created)
                )
                
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
