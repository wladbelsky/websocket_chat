from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: int):
        return await self.user_repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str):
        return await self.user_repository.get_by_email(email)

    async def create_user(self, name: str, email: str, password: str):
        from app.core.auth import get_password_hash
        hashed_password = get_password_hash(password)
        return await self.user_repository.create(name, email, hashed_password)

    async def authenticate_user(self, email: str, password: str):
        user = await self.get_user_by_email(email)
        if not user:
            return None
        from app.core.auth import verify_password
        if not verify_password(password, user.password):
            return None
        return user
