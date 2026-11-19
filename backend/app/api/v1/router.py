
from fastapi import APIRouter

from app.api.v1.endpoints import health, auth
from app.modules.access_control.router import router as access_control_router
from app.modules.equipment.router import router as equipment_router
from app.modules.projects.router import router as projects_router
from app.modules.quality.router import router as quality_router


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(access_control_router)
api_router.include_router(projects_router)
api_router.include_router(equipment_router)
api_router.include_router(quality_router)
