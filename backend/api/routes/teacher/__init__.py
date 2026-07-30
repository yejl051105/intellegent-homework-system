"""教师端路由聚合入口。"""

from fastapi import APIRouter

from backend.api.routes.teacher import criteria, exemplary, homework, review

router = APIRouter(prefix="/api/teacher", tags=["teacher"])
router.include_router(homework.router)
router.include_router(review.router)
router.include_router(criteria.router)
router.include_router(exemplary.router)
