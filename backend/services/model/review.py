"""模型评分结果的校验与可信坐标映射。"""

import json
import math

from backend.exceptions.system import ModelResponseError


def parse_review(content: str, ocr_document: dict) -> dict:
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ModelResponseError("模型没有返回可解析的评分结果，请重新生成。") from exc
    raw_score = payload.get("score")
    if isinstance(raw_score, bool):
        raise ModelResponseError("模型返回的分数格式无效，请重新生成。")
    try:
        score = int(raw_score)
    except (TypeError, ValueError) as exc:
        raise ModelResponseError("模型返回的分数格式无效，请重新生成。") from exc
    if not 0 <= score <= 100:
        raise ModelResponseError("模型返回的分数超出 0 到 100 的范围，请重新生成。")
    comment = str(payload.get("comment", "")).strip()
    if len(comment) < 30:
        raise ModelResponseError("模型返回的评语过短，请重新生成。")
    wrong_answers = payload.get("wrong_answers")
    if wrong_answers is None:
        wrong_answers = payload.get("error_items")
    return {
        "score": score,
        "comment": comment[:2000],
        "error_boxes": resolve_error_boxes(wrong_answers, ocr_document),
    }


def resolve_error_boxes(value: object, ocr_document: dict) -> list[dict]:
    if not isinstance(value, list):
        raise ModelResponseError("模型返回的错误标注格式无效，请重新生成。")
    try:
        image_width = float(ocr_document.get("image_width", 0))
        image_height = float(ocr_document.get("image_height", 0))
    except (TypeError, ValueError) as exc:
        raise ModelResponseError("OCR 缺少原图尺寸，无法定位错误标注。") from exc
    if not all(
        math.isfinite(number) and number > 0
        for number in (image_width, image_height)
    ):
        raise ModelResponseError("OCR 缺少原图尺寸，无法定位错误标注。")
    source_items = {
        str(item.get("id")): item
        for item in ocr_document.get("items", [])
        if isinstance(item, dict)
    }
    resolved = []
    selected_ids = set()
    for item in value[:12]:
        if not isinstance(item, dict):
            continue
        source_item = source_items.get(str(item.get("id")))
        if not source_item or str(source_item["id"]) in selected_ids:
            continue
        raw_deduction = item.get("deduction")
        if isinstance(raw_deduction, bool):
            raise ModelResponseError("模型返回的单项扣分格式无效，请重新生成。")
        try:
            deduction_number = float(raw_deduction)
        except (TypeError, ValueError) as exc:
            raise ModelResponseError("模型返回的单项扣分格式无效，请重新生成。") from exc
        if (
            not math.isfinite(deduction_number)
            or not deduction_number.is_integer()
            or not 1 <= deduction_number <= 100
        ):
            raise ModelResponseError(
                "模型返回的单项扣分必须是 1 到 100 的整数，请重新生成。"
            )
        box = source_item.get("bbox") or source_item.get("box", {})
        try:
            x = float(box["x"])
            y = float(box["y"])
            width = float(box["width"])
            height = float(box["height"])
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(number) for number in (x, y, width, height)):
            continue
        if (
            x < 0
            or y < 0
            or width <= 0
            or height <= 0
            or x >= image_width
            or y >= image_height
        ):
            continue
        selected_ids.add(str(source_item["id"]))
        resolved.append(
            {
                "ocr_id": source_item["id"],
                "bbox": expand_annotation_box(
                    x, y, width, height, image_width, image_height
                ),
                "coordinate_space": "source_pixel",
                "text": source_item.get("text", ""),
                "reason": str(item.get("reason", "错误答案")).strip()[:160]
                or "错误答案",
                "deduction": int(deduction_number),
            }
        )
    return resolved


def expand_annotation_box(
    x: float,
    y: float,
    width: float,
    height: float,
    image_width: float,
    image_height: float,
) -> dict:
    pad_x = min(max(width * 0.03, 6), min(36, image_width * 0.02))
    pad_y = min(max(height * 0.06, 6), min(28, image_height * 0.025))
    left = max(0, x - pad_x)
    top = max(0, y - pad_y)
    right = min(image_width, x + width + pad_x)
    bottom = min(image_height, y + height + pad_y)
    return {
        "x": round(left, 2),
        "y": round(top, 2),
        "width": round(max(1, right - left), 2),
        "height": round(max(1, bottom - top), 2),
    }
