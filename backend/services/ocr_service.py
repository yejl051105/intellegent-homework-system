import os
import posixpath
import uuid
from PIL import Image

from paddleocr import PaddleOCR, FormulaRecognition, FormulaRecognitionPipeline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ORIGINAL_FOLDER = os.path.join(UPLOAD_FOLDER, "original")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ORIGINAL_FOLDER, exist_ok=True)

ocr = PaddleOCR(lang="ch", use_textline_orientation=True)

_formula_recognizer = None
_formula_pipeline = None


def get_formula_recognizer():
    global _formula_recognizer
    if _formula_recognizer is None:
        _formula_recognizer = FormulaRecognition(model_name="PP-FormulaNet_plus-S")
    return _formula_recognizer


def get_formula_pipeline():
    global _formula_pipeline
    if _formula_pipeline is None:
        _formula_pipeline = FormulaRecognitionPipeline(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            formula_recognition_model_name="PP-FormulaNet_plus-S",
        )
    return _formula_pipeline


def crop_image(img: Image.Image, coord: list[float]) -> Image.Image:
    x1, y1, x2, y2 = map(int, coord)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img.width, x2), min(img.height, y2)
    return img.crop((x1, y1, x2, y2))


def ocr_region(img_pil: Image.Image, filepath: str) -> str:
    region_path = filepath.replace(".", "_region.")
    img_pil.save(region_path)
    try:
        result = ocr.predict(region_path)
        lines = []
        for item in result:
            lines.extend(item.get("rec_texts", []))
        return "".join(lines)
    finally:
        if os.path.exists(region_path):
            os.remove(region_path)


def extract_text(filepath: str) -> str:
    """Extract the text that will be supplied to the review model."""
    document = extract_text_document(filepath)
    return "\n".join(item["text"] for item in document["items"])


def get_image_metadata(filepath: str, file_path: str | None = None) -> dict:
    """Read metadata without changing the uploaded source bytes."""
    with Image.open(filepath) as source_image:
        image_width, image_height = source_image.size
        image_format = (source_image.format or "").lower()

    return {
        "original_width": image_width,
        "original_height": image_height,
        "format": image_format,
        "file_path": file_path or os.path.relpath(filepath, BASE_DIR).replace(os.sep, "/"),
    }


def adapt_paddleocr_result(result: dict, next_id: int, image_width: int, image_height: int) -> dict | None:
    """Convert one PaddleOCR result into the application's source-pixel contract."""
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
            x1, y1, x2, y2 = min(x_values), min(y_values), max(x_values), max(y_values)
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
    """Run PaddleOCR on the untouched original image and return source-pixel boxes."""
    image_metadata = get_image_metadata(filepath, file_path)
    image_width = image_metadata["original_width"]
    image_height = image_metadata["original_height"]

    items = []
    for result in ocr.predict(filepath):
        texts = result.get("rec_texts", [])
        for index in range(len(texts)):
            item = adapt_paddleocr_result(result, index, image_width, image_height)
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


def save_original_upload(filename: str, content: bytes) -> tuple[str, str, dict]:
    """Persist the exact upload under original/ and return relative path plus metadata."""
    suffix = os.path.splitext(filename or "image.jpg")[1].lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}:
        suffix = ".jpg"

    relative_path = posixpath.join("original", f"{uuid.uuid4().hex}{suffix}")
    filepath = os.path.join(UPLOAD_FOLDER, *relative_path.split("/"))
    with open(filepath, "wb") as output:
        output.write(content)
    try:
        metadata = get_image_metadata(filepath, relative_path)
    except Exception:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise
    return relative_path, filepath, metadata


def save_upload(image, upload_folder: str) -> str:
    ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    return filepath
