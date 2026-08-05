import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ideaforge.infrastructure.database.models.user import User
from ideaforge.api.schemas.user import UserCreate


class SQLUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        result = await self._session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def delete(self, user_id: uuid.UUID) -> bool:
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        await self._session.delete(user)
        await self._session.flush()
        return True
