"""OCR 结果适配与 source_pixel 文档构造。"""

import os

from PIL import Image

from backend.core.config import BASE_DIR
from backend.services.ocr.runtime import ocr


def get_image_metadata(filepath: str, file_path: str | None = None) -> dict:
    with Image.open(filepath) as source_image:
        image_width, image_height = source_image.size
        image_format = (source_image.format or "").lower()
    return {
        "original_width": image_width,
        "original_height": image_height,
        "format": image_format,
        "file_path": file_path
        or os.path.relpath(filepath, BASE_DIR).replace(os.sep, "/"),
    }


def adapt_paddleocr_result(
    result: dict,
    next_id: int,
    image_width: int,
    image_height: int,
) -> dict | None:
    texts = result.get("rec_texts", [])
    scores = result.get("rec_scores", [])
    boxes = result.get("rec_boxes", [])
    polygons = result.get("dt_polys", result.get("rec_polys", []))
    if next_id >= len(texts):
        return None
    text = str(texts[next_id]).strip()
    if not text:
        return None
    try:
        x1, y1, x2, y2 = (float(value) for value in boxes[next_id])
    except (IndexError, TypeError, ValueError):
        try:
            polygon = polygons[next_id]
            x_values = [float(point[0]) for point in polygon]
            y_values = [float(point[1]) for point in polygon]
            x1, y1 = min(x_values), min(y_values)
            x2, y2 = max(x_values), max(y_values)
        except (IndexError, TypeError, ValueError):
            return None
    x = max(0, min(x1, image_width - 1))
    y = max(0, min(y1, image_height - 1))
    width = max(1, min(x2 - x1, image_width - x))
    height = max(1, min(y2 - y1, image_height - y))
    try:
        confidence = round(float(scores[next_id]), 4) if next_id < len(scores) else None
    except (TypeError, ValueError, OverflowError):
        confidence = None
    return {
        "id": next_id + 1,
        "text": text,
        "confidence": confidence,
        "bbox": {
            "x": round(x, 2),
            "y": round(y, 2),
            "width": round(width, 2),
            "height": round(height, 2),
        },
    }


def extract_text_document(filepath: str, file_path: str | None = None) -> dict:
    image_metadata = get_image_metadata(filepath, file_path)
    image_width = image_metadata["original_width"]
    image_height = image_metadata["original_height"]
    items = []
    for result in ocr.predict(filepath):
        for index in range(len(result.get("rec_texts", []))):
            item = adapt_paddleocr_result(
                result, index, image_width, image_height
            )
            if item:
                item["id"] = len(items) + 1
                items.append(item)
    return {
        "coordinate_space": "source_pixel",
        "image_width": image_width,
        "image_height": image_height,
        "image": image_metadata,
        "items": items,
    }


def extract_text(filepath: str) -> str:
    document = extract_text_document(filepath)
    return "\n".join(item["text"] for item in document["items"])
