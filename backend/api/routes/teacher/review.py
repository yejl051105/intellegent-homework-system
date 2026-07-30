import math
import os

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from backend.api.deps import require_user
from backend.core.config import UPLOAD_DIR
from backend.exceptions.business import (
    BusinessConflictException,
    BusinessValidationException,
    ResourceNotFoundException,
)
from backend.exceptions.system import ThirdPartyServiceException
from backend.schemas.response import ApiResponse
from backend.services.criteria_service import extract_criteria_text
from backend.services.homework_service import (
    finalize_ai_review,
    get_criteria,
    get_homework,
    reset_ai_review,
    save_ai_review,
    save_ocr_document,
)
from backend.services.model_service import (
    generate_homework_review,
    get_model_options,
    get_model_settings,
)
from backend.services.ocr_service import extract_text_document
from backend.utils.response import success

router = APIRouter()


@router.get("/ai-models", response_model=ApiResponse)
async def api_teacher_ai_models(request: Request):
    require_user(request, "teacher")
    return success(data=get_model_options())


@router.post("/homework/{homework_id}/ai-review", response_model=ApiResponse)
async def api_teacher_generate_ai_review(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在")
    try:
        body = await request.json()
    except Exception as exc:
        raise BusinessValidationException(
            "请选择本次 AI 批改使用的文字评分标准。"
        ) from exc

    criteria_id = body.get("criteria_id")
    if isinstance(criteria_id, bool) or not isinstance(criteria_id, int):
        raise BusinessValidationException("请选择本次 AI 批改使用的文字评分标准。")
    criterion = next(
        (item for item in get_criteria() if item["id"] == criteria_id), None
    )
    if not criterion:
        raise BusinessValidationException("所选评分标准不存在或已被删除。")

    criteria_content = criterion.get("content", "").strip()
    if not criteria_content and criterion.get("filename"):
        criteria_path = os.path.join(UPLOAD_DIR, criterion["filename"])
        if not os.path.isfile(criteria_path):
            raise ResourceNotFoundException("未找到评分标准附件，无法生成 AI 建议。")
        criteria_content = await run_in_threadpool(extract_criteria_text, criteria_path)
    if not criteria_content:
        raise BusinessValidationException("请先添加文字或附件评分标准。")

    model_id = body.get("model_id")
    if not isinstance(model_id, str) or not model_id:
        raise BusinessValidationException("请选择本次 AI 批改使用的评分模型。")
    settings = get_model_settings(model_id)

    filepath = os.path.join(UPLOAD_DIR, homework.get("filename", ""))
    if not homework.get("filename") or not os.path.isfile(filepath):
        raise ResourceNotFoundException("未找到作业图片，无法生成 AI 建议。")

    ocr_document = homework.get("ocr_document")
    if not isinstance(ocr_document, dict) or not ocr_document.get("items"):
        try:
            ocr_document = await run_in_threadpool(
                extract_text_document,
                filepath,
                homework.get("original_file_path") or homework.get("filename"),
            )
        except Exception as exc:
            raise ThirdPartyServiceException(
                "作业文字识别失败，暂时无法生成错误标注。"
            ) from exc
        if not ocr_document.get("items"):
            raise BusinessValidationException(
                "未识别到可供定位的作业文字，请检查上传图片。"
            )
        save_ocr_document(homework_id, ocr_document)

    criteria_text = f"【{criterion['title']}】\n{criteria_content}"
    review = await generate_homework_review(
        settings, homework["title"], criteria_text, ocr_document
    )
    result = save_ai_review(
        homework_id,
        review,
        f"{settings.label} · {settings.model}",
        criterion,
    )
    return success(data=result)


@router.post("/homework/{homework_id}/reset-review", response_model=ApiResponse)
async def api_teacher_reset_ai_review(request: Request, homework_id: int):
    require_user(request, "teacher")
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在")
    return success(data=reset_ai_review(homework_id))


def _validate_error_boxes(error_boxes: object, ocr_document: dict) -> list[dict]:
    if not isinstance(error_boxes, list) or len(error_boxes) > 12:
        raise BusinessValidationException("错误标注最多 12 个，且必须是矩形数组。")
    try:
        image_width = float(ocr_document["image_width"])
        image_height = float(ocr_document["image_height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BusinessValidationException("OCR 缺少原图尺寸，无法校验错误标注。") from exc
    if not all(math.isfinite(value) and value > 0 for value in (image_width, image_height)):
        raise BusinessValidationException("OCR 原图尺寸无效，无法校验错误标注。")

    source_pixel_boxes = []
    for item in error_boxes:
        if not isinstance(item, dict):
            raise BusinessValidationException("错误标注格式无效。")
        if item.get("coordinate_space") != "source_pixel":
            raise BusinessValidationException("错误标注必须使用原图像素坐标。")
        box = item.get("bbox") or item
        try:
            x, y = float(box["x"]), float(box["y"])
            width, height = float(box["width"]), float(box["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BusinessValidationException("错误标注坐标无效。") from exc
        coordinates = (x, y, width, height)
        if not all(math.isfinite(value) for value in coordinates):
            raise BusinessValidationException("错误标注坐标无效。")
        if (
            x < 0
            or y < 0
            or width <= 0
            or height <= 0
            or x + width > image_width + 0.01
            or y + height > image_height + 0.01
        ):
            raise BusinessValidationException("错误标注必须位于作业图片范围内。")
        annotation = {
            "bbox": {
                "x": round(x, 2),
                "y": round(y, 2),
                "width": round(width, 2),
                "height": round(height, 2),
            },
            "coordinate_space": "source_pixel",
            "text": str(item.get("text", "")).strip()[:500],
            "reason": str(item.get("reason", "错误答案")).strip()[:160]
            or "错误答案",
        }
        deduction = item.get("deduction")
        if deduction is not None:
            if (
                isinstance(deduction, bool)
                or not isinstance(deduction, int)
                or not 1 <= deduction <= 100
            ):
                raise BusinessValidationException("单项扣分必须是 1 到 100 的整数。")
            annotation["deduction"] = deduction
        if item.get("ocr_id") is not None:
            annotation["ocr_id"] = item["ocr_id"]
        source_pixel_boxes.append(annotation)
    return source_pixel_boxes


@router.post("/grade/{homework_id}", response_model=ApiResponse)
async def api_teacher_grade(request: Request, homework_id: int):
    user = require_user(request, "teacher")
    body = await request.json()
    homework = get_homework(homework_id, role="teacher")
    if not homework:
        raise ResourceNotFoundException("作业不存在")
    if (
        homework.get("review_status") != "ai_suggested"
        or homework.get("ai_score") is None
    ):
        raise BusinessConflictException("请先生成 AI 评分建议并完成教师复核。")

    score = body.get("score")
    comment = body.get("comment", "")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise BusinessValidationException("分数必须是 0 到 100 的整数。")
    if not isinstance(comment, str) or not comment.strip():
        raise BusinessValidationException("请填写教师评语后再完成复核。")
    source_pixel_boxes = _validate_error_boxes(
        body.get("error_boxes", []), homework.get("ocr_document") or {}
    )
    result = finalize_ai_review(
        homework_id,
        score,
        comment.strip()[:2000],
        source_pixel_boxes,
        user,
    )
    return success(data=result)
