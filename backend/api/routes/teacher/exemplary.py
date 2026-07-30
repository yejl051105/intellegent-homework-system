import os
import shutil
import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile

from backend.api.deps import require_user
from backend.api.serializers import exemplary_payload
from backend.core.config import UPLOAD_DIR
from backend.exceptions.business import ResourceNotFoundException
from backend.schemas.response import ApiResponse
from backend.services.homework_service import (
    create_exemplary,
    delete_exemplary,
    get_exemplary,
    get_homework,
    get_homeworks,
    set_exemplary,
)
from backend.utils.response import success

router = APIRouter()


@router.get("/exemplary", response_model=ApiResponse)
async def api_teacher_exemplary_list(request: Request):
    require_user(request, "teacher")
    homeworks = [
        exemplary_payload(homework)
        for homework in get_homeworks(role="teacher")
        if homework.get("is_exemplary")
    ]
    return success(data={"homeworks": homeworks})


@router.get("/exemplary/{homework_id}", response_model=ApiResponse)
async def api_teacher_exemplary_detail(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = get_homework(homework_id, role="teacher")
    if not homework or not homework.get("is_exemplary"):
        raise ResourceNotFoundException("优秀作业不存在")
    return success(data=exemplary_payload(homework))


@router.post("/exemplary/upload", response_model=ApiResponse)
async def api_teacher_upload_exemplary(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
):
    require_user(request, "teacher")
    ext = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    content = await image.read()
    with open(save_path, "wb") as output:
        output.write(content)
    return success(data=create_exemplary(title, unique_name, description))


@router.post("/exemplary/{exemplary_id}/delete", response_model=ApiResponse)
async def api_teacher_delete_exemplary(request: Request, exemplary_id: int):
    require_user(request, "teacher")
    delete_exemplary(exemplary_id)
    return success(data={"ok": True})


@router.post("/exemplary/{homework_id}", response_model=ApiResponse)
async def api_teacher_exemplary(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在")
    source_path = os.path.join(UPLOAD_DIR, homework["filename"])
    ext = os.path.splitext(homework["filename"])[1] or ".jpg"
    new_name = f"{uuid.uuid4().hex}{ext}"
    destination_path = os.path.join(UPLOAD_DIR, new_name)
    if os.path.exists(source_path):
        shutil.copy2(source_path, destination_path)
    description = (
        f"学生：{homework['student_name']}，得分：{homework['score']}"
        if homework["score"] is not None
        else f"学生：{homework['student_name']}"
    )
    create_exemplary(homework["title"], new_name, description)
    set_exemplary(homework_id, True)
    return success(data={"ok": True, "exemplary_title": homework["title"]})


@router.post("/unexemplary/{homework_id}", response_model=ApiResponse)
async def api_teacher_unexemplary(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在")
    for item in get_exemplary():
        if item["title"] == homework["title"] and item.get(
            "description", ""
        ).startswith(f"学生：{homework['student_name']}"):
            delete_exemplary(item["id"])
            break
    set_exemplary(homework_id, False)
    return success(data={"ok": True})
