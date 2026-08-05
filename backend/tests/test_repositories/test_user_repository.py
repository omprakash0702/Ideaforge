import pytest

from ideaforge.api.schemas.user import UserCreate
from ideaforge.infrastructure.repositories.user_repository import SQLUserRepository


@pytest.mark.asyncio
async def test_create_user(user_repo: SQLUserRepository) -> None:
    data = UserCreate(name="Alice", email="alice@example.com")
    user = await user_repo.create(data)

    assert user.id is not None
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_get_by_id(user_repo: SQLUserRepository) -> None:
    user = await user_repo.create(UserCreate(name="Bob", email="bob@example.com"))
    fetched = await user_repo.get_by_id(user.id)

    assert fetched is not None
    assert fetched.id == user.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(user_repo: SQLUserRepository) -> None:
    import uuid
    result = await user_repo.get_by_id(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_by_email(user_repo: SQLUserRepository) -> None:
    await user_repo.create(UserCreate(name="Carol", email="carol@example.com"))
    found = await user_repo.get_by_email("carol@example.com")

    assert found is not None
    assert found.name == "Carol"


@pytest.mark.asyncio
async def test_get_by_email_not_found(user_repo: SQLUserRepository) -> None:
    result = await user_repo.get_by_email("nobody@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_list_all(user_repo: SQLUserRepository) -> None:
    await user_repo.create(UserCreate(name="Dan", email="dan@example.com"))
    await user_repo.create(UserCreate(name="Eve", email="eve@example.com"))
    users = await user_repo.list_all()

    assert len(users) >= 2


@pytest.mark.asyncio
async def test_delete_user(user_repo: SQLUserRepository) -> None:
    user = await user_repo.create(UserCreate(name="Frank", email="frank@example.com"))
    deleted = await user_repo.delete(user.id)

    assert deleted is True
    assert await user_repo.get_by_id(user.id) is None


@pytest.mark.asyncio
async def test_delete_nonexistent_user(user_repo: SQLUserRepository) -> None:
    import uuid
    result = await user_repo.delete(uuid.uuid4())
    assert result is False
