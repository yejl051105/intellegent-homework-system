import os
import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.api.deps import require_user
from backend.core.config import UPLOAD_DIR
from backend.exceptions.business import (
    BusinessValidationException,
    CriteriaExtractionError,
)
from backend.schemas.response import ApiResponse
from backend.services.criteria_service import extract_criteria_text
from backend.services.homework_service import create_criteria, delete_criteria, get_criteria
from backend.utils.response import success

router = APIRouter()


@router.get("/criteria", response_model=ApiResponse)
async def api_teacher_criteria(request: Request):
    require_user(request, "teacher")
    return success(data=get_criteria())


@router.post("/criteria", response_model=ApiResponse)
async def api_teacher_add_criteria(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    file: UploadFile | None = File(None),
):
    require_user(request, "teacher")
    title = title.strip()
    text_content = content.strip()
    if not title:
        raise BusinessValidationException("请输入评分标准标题。")
    if len(text_content) > 12000:
        raise BusinessValidationException("文字评分标准不能超过 12000 个字符。")
    if text_content and file:
        raise BusinessValidationException("一次只能提交文字标准或附件标准。")
    if not text_content and not file:
        raise BusinessValidationException("请粘贴文字评分标准或选择一个附件。")

    unique_name = ""
    extracted_content = text_content
    if file:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in {".pdf", ".doc", ".docx"}:
            raise BusinessValidationException("附件仅支持 PDF、DOC、DOCX 格式。")
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(UPLOAD_DIR, unique_name)
        file_content = await file.read()
        with open(save_path, "wb") as output:
            output.write(file_content)
        try:
            extracted_content = await run_in_threadpool(extract_criteria_text, save_path)
        except CriteriaExtractionError:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise

    criterion = create_criteria(
        title, unique_name, extracted_content, "file" if file else "text"
    )
    return success(data=criterion)


@router.post("/criteria/{criteria_id}/delete", response_model=ApiResponse)
async def api_teacher_delete_criteria(request: Request, criteria_id: int):
    require_user(request, "teacher")
    delete_criteria(criteria_id)
    return success(data={"ok": True})
