from fastapi import APIRouter, Request

from backend.api.deps import require_user
from backend.exceptions.business import ResourceNotFoundException
from backend.schemas.response import ApiResponse
from backend.services.homework_service import (
    delete_homework,
    get_deleted_homeworks,
    get_homework,
    get_homeworks,
    permanently_delete_homework,
    remove_homework_files,
    restore_homework,
)
from backend.utils.response import success

router = APIRouter()


@router.get("/homeworks", response_model=ApiResponse)
async def api_teacher_homeworks(request: Request):
    require_user(request, "teacher")
    return success(data=get_homeworks(role="teacher"))


@router.post("/homework/{homework_id}/delete", response_model=ApiResponse)
async def api_teacher_delete_homework(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = delete_homework(homework_id, "teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在或已经在回收站。")
    return success(data={"ok": True, "homework_id": homework_id})


@router.get("/recycle-bin", response_model=ApiResponse)
async def api_teacher_recycle_bin(request: Request):
    require_user(request, "teacher")
    return success(data=get_deleted_homeworks("teacher"))


@router.post("/homework/{homework_id}/restore", response_model=ApiResponse)
async def api_teacher_restore_homework(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = restore_homework(homework_id, "teacher")
    if not homework:
        raise ResourceNotFoundException("回收站中不存在该作业。")
    return success(data={"ok": True, "homework_id": homework_id})


@router.delete("/homework/{homework_id}/permanent", response_model=ApiResponse)
async def api_teacher_permanently_delete_homework(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework, fully_removed = permanently_delete_homework(homework_id, "teacher")
    if not homework:
        raise ResourceNotFoundException("回收站中不存在该作业。")
    if fully_removed:
        remove_homework_files(homework)
    return success(data={"ok": True, "homework_id": homework_id})


@router.get("/homework/{homework_id}", response_model=ApiResponse)
async def api_teacher_homework(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在")
    return success(data=homework)
