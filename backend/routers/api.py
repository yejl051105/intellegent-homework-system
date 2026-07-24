import os
import uuid

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from backend.services.model_service import (
    ModelConfigurationError,
    ModelResponseError,
    generate_homework_review,
    get_model_options,
    get_model_settings,
)
from backend.services.ocr_service import BASE_DIR, extract_text_document
from backend.services.criteria_service import CriteriaExtractionError, extract_criteria_text
from backend.services.auth_service import authenticate
from backend.services.permission_service import get_route_permissions
from backend.services.homework_service import (
    get_homeworks,
    get_deleted_homeworks,
    get_homework,
    create_homework,
    finalize_ai_review,
    set_exemplary,
    get_criteria,
    create_criteria,
    delete_criteria,
    get_exemplary,
    create_exemplary,
    delete_exemplary,
    save_ai_review,
    reset_ai_review,
    save_ocr_document,
    delete_homework,
    restore_homework,
    permanently_delete_homework,
    remove_related_exemplary,
)

router = APIRouter(prefix="/api", tags=["api"])
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_user(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user


def require_user(request: Request, role: str | None = None):
    user = get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if role and user["role"] != role:
        raise HTTPException(status_code=403, detail="无权访问该资源")
    return user


def student_payload(homework: dict):
    """Never expose unreviewed model suggestions to the student."""
    return {
        key: value
        for key, value in homework.items()
        if not key.startswith("ai_") and key not in {"review_status", "reviewed_by"}
    }


def exemplary_payload(homework: dict):
    """Expose only reviewed fields needed by the exemplary-work gallery."""
    allowed_fields = {
        "id",
        "student_name",
        "title",
        "filename",
        "score",
        "comment",
        "is_exemplary",
        "submitted_at",
        "graded_at",
    }
    return {key: value for key, value in homework.items() if key in allowed_fields}


def remove_homework_files(homework: dict):
    filenames = [homework.get("filename", "")]
    filenames.extend(item.get("filename", "") for item in remove_related_exemplary(homework))
    for filename in filenames:
        if filename:
            path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(path):
                os.remove(path)


# ── Auth ──

@router.post("/login")
async def api_login(request: Request):
    body = await request.json()
    user = authenticate(body.get("username", ""), body.get("password", ""))
    if not user:
        return JSONResponse({"detail": "用户名或密码错误"}, status_code=401)
    request.session["user"] = user
    return user


@router.post("/logout")
async def api_logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
async def api_me(request: Request):
    user = get_user(request)
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return user


@router.get("/routes")
async def api_routes(request: Request):
    user = require_user(request)
    permissions = get_route_permissions(user)
    if not permissions:
        raise HTTPException(status_code=403, detail="当前账号没有可用权限")
    return permissions


# ── Student ──

@router.get("/student/homeworks")
async def api_student_homeworks(request: Request):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return [student_payload(h) for h in get_homeworks({"student_id": user["id"]}, role="student")]


@router.get("/student/homework/{homework_id}")
async def api_student_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)

    homework = get_homework(homework_id, role="student")
    if not homework or homework["student_id"] != user["id"]:
        # Treat another student's work as nonexistent to avoid exposing record ownership.
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    return student_payload(homework)


@router.post("/student/homework/{homework_id}/delete")
async def api_student_delete_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = get_homework(homework_id, role="student")
    if not homework or homework.get("student_id") != user["id"]:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    delete_homework(homework_id, "student")
    return {"ok": True, "homework_id": homework_id}


@router.get("/student/recycle-bin")
async def api_student_recycle_bin(request: Request):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return get_deleted_homeworks("student", {"student_id": user["id"]})


@router.post("/student/homework/{homework_id}/restore")
async def api_student_restore_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = get_homework(homework_id, include_deleted=True, role="student")
    if not homework or homework.get("student_id") != user["id"]:
        return JSONResponse({"detail": "回收站中不存在该作业。"}, status_code=404)
    if not restore_homework(homework_id, "student"):
        return JSONResponse({"detail": "回收站中不存在该作业。"}, status_code=404)
    return {"ok": True, "homework_id": homework_id}


@router.delete("/student/homework/{homework_id}/permanent")
async def api_student_permanently_delete_homework(request: Request, homework_id: int):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = get_homework(homework_id, include_deleted=True, role="student")
    if not homework or homework.get("student_id") != user["id"]:
        return JSONResponse({"detail": "回收站中不存在该作业。"}, status_code=404)
    deleted, fully_removed = permanently_delete_homework(homework_id, "student")
    if not deleted:
        return JSONResponse({"detail": "回收站中不存在该作业。"}, status_code=404)
    if fully_removed:
        remove_homework_files(deleted)
    return {"ok": True, "homework_id": homework_id}


@router.post("/student/upload")
async def api_student_upload(
    request: Request,
    title: str = Form(...),
    image: UploadFile = File(...),
):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)

    ext = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    content = await image.read()
    with open(save_path, "wb") as f:
        f.write(content)

    hw = create_homework(
        student_id=user["id"],
        student_name=user["name"],
        title=title,
        filename=unique_name,
    )
    return hw


@router.get("/student/exemplary")
async def api_student_exemplary(request: Request):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return [exemplary_payload(h) for h in get_homeworks() if h.get("is_exemplary")]


@router.get("/student/exemplary/{homework_id}")
async def api_student_exemplary_detail(request: Request, homework_id: int):
    user = require_user(request, "student")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = get_homework(homework_id)
    if not homework or not homework.get("is_exemplary"):
        return JSONResponse({"detail": "优秀作业不存在"}, status_code=404)
    return exemplary_payload(homework)


# ── Teacher ──

@router.get("/teacher/homeworks")
async def api_teacher_homeworks(request: Request):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return get_homeworks(role="teacher")


@router.post("/teacher/homework/{homework_id}/delete")
async def api_teacher_delete_homework(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = delete_homework(homework_id, "teacher")
    if not homework:
        return JSONResponse({"detail": "作业不存在或已经在回收站。"}, status_code=404)
    return {"ok": True, "homework_id": homework_id}


@router.get("/teacher/recycle-bin")
async def api_teacher_recycle_bin(request: Request):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return get_deleted_homeworks("teacher")


@router.post("/teacher/homework/{homework_id}/restore")
async def api_teacher_restore_homework(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = restore_homework(homework_id, "teacher")
    if not homework:
        return JSONResponse({"detail": "回收站中不存在该作业。"}, status_code=404)
    return {"ok": True, "homework_id": homework_id}


@router.delete("/teacher/homework/{homework_id}/permanent")
async def api_teacher_permanently_delete_homework(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework, fully_removed = permanently_delete_homework(homework_id, "teacher")
    if not homework:
        return JSONResponse({"detail": "回收站中不存在该作业。"}, status_code=404)
    if fully_removed:
        remove_homework_files(homework)
    return {"ok": True, "homework_id": homework_id}


@router.get("/teacher/ai-models")
async def api_teacher_ai_models(request: Request):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return get_model_options()


@router.get("/teacher/homework/{homework_id}")
async def api_teacher_homework(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    hw = get_homework(homework_id, role="teacher")
    if not hw:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    return hw


@router.post("/teacher/homework/{homework_id}/ai-review")
async def api_teacher_generate_ai_review(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)

    homework = get_homework(homework_id, role="teacher")
    if not homework:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "请选择本次 AI 批改使用的文字评分标准。"}, status_code=422)

    criteria_id = body.get("criteria_id")
    if isinstance(criteria_id, bool) or not isinstance(criteria_id, int):
        return JSONResponse({"detail": "请选择本次 AI 批改使用的文字评分标准。"}, status_code=422)
    criterion = next((item for item in get_criteria() if item["id"] == criteria_id), None)
    if not criterion:
        return JSONResponse({"detail": "所选评分标准不存在或已被删除。"}, status_code=422)

    criteria_content = criterion.get("content", "").strip()
    if not criteria_content and criterion.get("filename"):
        criteria_path = os.path.join(UPLOAD_FOLDER, criterion["filename"])
        if not os.path.isfile(criteria_path):
            return JSONResponse({"detail": "未找到评分标准附件，无法生成 AI 建议。"}, status_code=404)
        try:
            criteria_content = await run_in_threadpool(extract_criteria_text, criteria_path)
        except CriteriaExtractionError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
    if not criteria_content:
        return JSONResponse({"detail": "请先添加文字或附件评分标准。"}, status_code=422)

    model_id = body.get("model_id")
    if not isinstance(model_id, str) or not model_id:
        return JSONResponse({"detail": "请选择本次 AI 批改使用的评分模型。"}, status_code=422)

    try:
        settings = get_model_settings(model_id)
    except ModelConfigurationError as exc:
        status_code = 422 if model_id not in {"deepseek", "openai", "gemini"} else 503
        return JSONResponse({"detail": str(exc)}, status_code=status_code)

    filepath = os.path.join(UPLOAD_FOLDER, homework.get("filename", ""))
    if not homework.get("filename") or not os.path.isfile(filepath):
        return JSONResponse({"detail": "未找到作业图片，无法生成 AI 建议。"}, status_code=404)

    ocr_document = homework.get("ocr_document")
    if not isinstance(ocr_document, dict) or not ocr_document.get("items"):
        try:
            ocr_document = await run_in_threadpool(extract_text_document, filepath)
        except Exception:
            return JSONResponse({"detail": "作业文字识别失败，暂时无法生成错误标注。"}, status_code=422)
        if not ocr_document.get("items"):
            return JSONResponse({"detail": "未识别到可供定位的作业文字，请检查上传图片。"}, status_code=422)
        save_ocr_document(homework_id, ocr_document)

    criteria_text = f"【{criterion['title']}】\n{criteria_content}"
    try:
        review = await generate_homework_review(
            settings,
            homework["title"],
            criteria_text,
            ocr_document,
        )
    except ModelResponseError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)

    return save_ai_review(homework_id, review, f"{settings.label} · {settings.model}", criterion)


@router.post("/teacher/homework/{homework_id}/reset-review")
async def api_teacher_reset_ai_review(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    return reset_ai_review(homework_id)


@router.post("/teacher/grade/{homework_id}")
async def api_teacher_grade(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    body = await request.json()
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    if homework.get("review_status") != "ai_suggested" or homework.get("ai_score") is None:
        return JSONResponse({"detail": "请先生成 AI 评分建议并完成教师复核。"}, status_code=409)

    score = body.get("score")
    comment = body.get("comment", "")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        return JSONResponse({"detail": "分数必须是 0 到 100 的整数。"}, status_code=422)
    if not isinstance(comment, str) or not comment.strip():
        return JSONResponse({"detail": "请填写教师评语后再完成复核。"}, status_code=422)
    error_boxes = body.get("error_boxes", [])
    if not isinstance(error_boxes, list) or len(error_boxes) > 12:
        return JSONResponse({"detail": "错误标注最多 12 个，且必须是矩形数组。"}, status_code=422)
    normalized_boxes = []
    for item in error_boxes:
        if not isinstance(item, dict):
            return JSONResponse({"detail": "错误标注格式无效。"}, status_code=422)
        try:
            x, y = float(item["x"]), float(item["y"])
            width, height = float(item["width"]), float(item["height"])
        except (KeyError, TypeError, ValueError):
            return JSONResponse({"detail": "错误标注坐标无效。"}, status_code=422)
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1000 or y + height > 1000:
            return JSONResponse({"detail": "错误标注必须位于作业图片范围内。"}, status_code=422)
        normalized_boxes.append({"x": round(x, 2), "y": round(y, 2), "width": round(width, 2), "height": round(height, 2), "text": str(item.get("text", "")).strip()[:500], "reason": str(item.get("reason", "错误答案")).strip()[:160] or "错误答案"})

    hw = finalize_ai_review(homework_id, score, comment.strip()[:2000], normalized_boxes, user)
    return hw


@router.get("/teacher/criteria")
async def api_teacher_criteria(request: Request):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    return get_criteria()


@router.post("/teacher/criteria")
async def api_teacher_add_criteria(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    file: UploadFile | None = File(None),
):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    title = title.strip()
    text_content = content.strip()
    if not title:
        return JSONResponse({"detail": "请输入评分标准标题。"}, status_code=422)
    if len(text_content) > 12000:
        return JSONResponse({"detail": "文字评分标准不能超过 12000 个字符。"}, status_code=422)
    if text_content and file:
        return JSONResponse({"detail": "一次只能提交文字标准或附件标准。"}, status_code=422)
    if not text_content and not file:
        return JSONResponse({"detail": "请粘贴文字评分标准或选择一个附件。"}, status_code=422)

    unique_name = ""
    extracted_content = text_content
    if file:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in {".pdf", ".doc", ".docx"}:
            return JSONResponse({"detail": "附件仅支持 PDF、DOC、DOCX 格式。"}, status_code=422)
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_name)
        file_content = await file.read()
        with open(save_path, "wb") as f:
            f.write(file_content)

        try:
            extracted_content = await run_in_threadpool(extract_criteria_text, save_path)
        except CriteriaExtractionError as exc:
            if os.path.exists(save_path):
                os.remove(save_path)
            return JSONResponse({"detail": str(exc)}, status_code=422)

    c = create_criteria(title, unique_name, extracted_content, "file" if file else "text")
    return c


@router.post("/teacher/criteria/{criteria_id}/delete")
async def api_teacher_delete_criteria(request: Request, criteria_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    delete_criteria(criteria_id)
    return {"ok": True}


@router.get("/teacher/exemplary")
async def api_teacher_exemplary_list(request: Request):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    hw_list = [exemplary_payload(h) for h in get_homeworks(role="teacher") if h.get("is_exemplary")]
    return {"homeworks": hw_list}


@router.get("/teacher/exemplary/{homework_id}")
async def api_teacher_exemplary_detail(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    homework = get_homework(homework_id, role="teacher")
    if not homework or not homework.get("is_exemplary"):
        return JSONResponse({"detail": "优秀作业不存在"}, status_code=404)
    return exemplary_payload(homework)


@router.post("/teacher/exemplary/upload")
async def api_teacher_upload_exemplary(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)

    ext = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    content = await image.read()
    with open(save_path, "wb") as f:
        f.write(content)

    e = create_exemplary(title, unique_name, description)
    return e


@router.post("/teacher/exemplary/{exemplary_id}/delete")
async def api_teacher_delete_exemplary(request: Request, exemplary_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    delete_exemplary(exemplary_id)
    return {"ok": True}


@router.post("/teacher/exemplary/{homework_id}")
async def api_teacher_exemplary(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    hw = get_homework(homework_id, role="teacher")
    if not hw:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    # Copy file to create a standalone exemplary entry
    src_path = os.path.join(UPLOAD_FOLDER, hw["filename"])
    ext = os.path.splitext(hw["filename"])[1] or ".jpg"
    new_name = f"{uuid.uuid4().hex}{ext}"
    dst_path = os.path.join(UPLOAD_FOLDER, new_name)
    if os.path.exists(src_path):
        import shutil
        shutil.copy2(src_path, dst_path)
    desc = f"学生：{hw['student_name']}，得分：{hw['score']}" if hw["score"] is not None else f"学生：{hw['student_name']}"
    create_exemplary(hw["title"], new_name, desc)
    # Also set the flag on the homework record
    set_exemplary(homework_id, True)
    return {"ok": True, "exemplary_title": hw["title"]}


@router.post("/teacher/unexemplary/{homework_id}")
async def api_teacher_unexemplary(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    if not user:
        return JSONResponse({"detail": "未登录"}, status_code=401)
    hw = get_homework(homework_id, role="teacher")
    if not hw:
        return JSONResponse({"detail": "作业不存在"}, status_code=404)
    # Remove the standalone exemplary entry if it exists
    items = get_exemplary()
    for e in items:
        if e["title"] == hw["title"] and e.get("description", "").startswith(f"学生：{hw['student_name']}"):
            delete_exemplary(e["id"])
            break
    set_exemplary(homework_id, False)
    return {"ok": True}
