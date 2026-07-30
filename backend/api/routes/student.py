import os

from fastapi import APIRouter, File, Form, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.api.deps import require_user
from backend.api.serializers import exemplary_payload, student_payload
from backend.exceptions.business import (
    BusinessException,
    ResourceNotFoundException,
)
from backend.exceptions.system import ThirdPartyServiceException
from backend.schemas.response import ApiResponse
from backend.services.homework_service import (
    create_homework,
    delete_homework,
    get_deleted_homeworks,
    get_homework,
    get_homeworks,
    permanently_delete_homework,
    remove_homework_files,
    restore_homework,
)
from backend.services.ocr_service import extract_text_document, save_original_upload
from backend.utils.response import success

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/homeworks", response_model=ApiResponse)
async def api_student_homeworks(request: Request):
    user = require_user(request, "student")
    return success(data=[student_payload(h) for h in get_homeworks({"student_id": user["id"]}, role="student")])


@router.get("/homework/{homework_id}", response_model=ApiResponse)
async def api_student_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    homework = get_homework(homework_id, role="student")
    if not homework or homework["student_id"] != user["id"]:
        raise ResourceNotFoundException("作业不存在")
    return success(data=student_payload(homework))


@router.post("/homework/{homework_id}/delete", response_model=ApiResponse)
async def api_student_delete_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    homework = get_homework(homework_id, role="student")
    if not homework or homework.get("student_id") != user["id"]:
        raise ResourceNotFoundException("作业不存在")
    delete_homework(homework_id, "student")
    return success(data={"ok": True, "homework_id": homework_id})


@router.get("/recycle-bin", response_model=ApiResponse)
async def api_student_recycle_bin(request: Request):
    user = require_user(request, "student")
    return success(data=get_deleted_homeworks("student", {"student_id": user["id"]}))


@router.post("/homework/{homework_id}/restore", response_model=ApiResponse)
async def api_student_restore_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    homework = get_homework(homework_id, include_deleted=True, role="student")
    if not homework or homework.get("student_id") != user["id"]:
        raise ResourceNotFoundException("回收站中不存在该作业。")
    if not restore_homework(homework_id, "student"):
        raise ResourceNotFoundException("回收站中不存在该作业。")
    return success(data={"ok": True, "homework_id": homework_id})


@router.delete("/homework/{homework_id}/permanent", response_model=ApiResponse)
async def api_student_permanently_delete_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    homework = get_homework(homework_id, include_deleted=True, role="student")
    if not homework or homework.get("student_id") != user["id"]:
        raise ResourceNotFoundException("回收站中不存在该作业。")
    deleted, fully_removed = permanently_delete_homework(homework_id, "student")
    if not deleted:
        raise ResourceNotFoundException("回收站中不存在该作业。")
    if fully_removed:
        remove_homework_files(deleted)
    return success(data={"ok": True, "homework_id": homework_id})


@router.post("/upload", response_model=ApiResponse)
async def api_student_upload(
    request: Request,
    title: str = Form(...),
    image: UploadFile = File(...),
):
    user = require_user(request, "student")

    content = await image.read()
    if not content:
        raise BusinessException(message="上传文件为空。")

    save_path = None
    try:
        unique_name, save_path, image_metadata = save_original_upload(image.filename, content)
        ocr_document = await run_in_threadpool(extract_text_document, save_path, unique_name)
    except Exception as exc:
        if save_path and os.path.isfile(save_path):
            os.remove(save_path)
        message = "上传图片不是有效的图片文件。" if "cannot identify image" in str(exc).lower() else "原图文字识别失败，请检查图片后重试。"
        if "cannot identify image" in str(exc).lower():
            raise BusinessException(message=message) from exc
        raise ThirdPartyServiceException(message) from exc

    hw = create_homework(
        student_id=user["id"],
        student_name=user["name"],
        title=title,
        filename=unique_name,
        ocr_document=ocr_document,
        image_metadata=image_metadata,
    )
    return success(data=hw)


@router.get("/exemplary", response_model=ApiResponse)
async def api_student_exemplary(request: Request):
    require_user(request, "student")
    return success(data=[exemplary_payload(h) for h in get_homeworks() if h.get("is_exemplary")])


@router.get("/exemplary/{homework_id}", response_model=ApiResponse)
async def api_student_exemplary_detail(request: Request, homework_id: int):
    require_user(request, "student")
    homework = get_homework(homework_id)
    if not homework or not homework.get("is_exemplary"):
        raise ResourceNotFoundException("优秀作业不存在")
    return success(data=exemplary_payload(homework))
