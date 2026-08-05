from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ideaforge.infrastructure.database.models.user import User
    from ideaforge.api.schemas.user import UserCreate


class IUserRepository(Protocol):
    async def create(self, data: UserCreate) -> User: ...

    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def list_all(self) -> list[User]: ...

    async def delete(self, user_id: uuid.UUID) -> bool: ...
