"""应用路由聚合入口。"""

from fastapi import APIRouter

from backend.api.routes import auth, recognition, student, teacher

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(student.router)
api_router.include_router(teacher.router)
api_router.include_router(recognition.router)
