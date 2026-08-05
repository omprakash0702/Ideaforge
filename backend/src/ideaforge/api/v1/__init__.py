from fastapi import APIRouter

from ideaforge.api.v1.health import router as health_router
from ideaforge.api.v1.users import router as users_router
from ideaforge.api.v1.projects import router as projects_router
from ideaforge.api.v1.documents import router as documents_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router)
v1_router.include_router(users_router)
v1_router.include_router(projects_router)
v1_router.include_router(documents_router)
