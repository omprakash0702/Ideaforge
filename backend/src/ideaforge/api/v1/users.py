import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from ideaforge.api.dependencies import ProjectRepo, UserRepo
from ideaforge.api.schemas.project import ProjectResponse
from ideaforge.api.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, user_repo: UserRepo) -> UserResponse:
    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email '{body.email}' already exists.",
        )
    try:
        user = await user_repo.create(body)
    except IntegrityError:
        # Race: concurrent registration with the same email won the insert
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email '{body.email}' already exists.",
        )
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, user_repo: UserRepo) -> UserResponse:
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.get("/{user_id}/projects", response_model=list[ProjectResponse])
async def list_user_projects(
    user_id: uuid.UUID,
    user_repo: UserRepo,
    project_repo: ProjectRepo,
) -> list[ProjectResponse]:
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    projects = await project_repo.list_by_user(user_id)
    return [ProjectResponse.model_validate(p) for p in projects]
