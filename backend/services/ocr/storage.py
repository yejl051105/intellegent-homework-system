"""OCR 上传文件保存。"""

import os
import posixpath
import uuid

from backend.core.config import ORIGINAL_UPLOAD_DIR, UPLOAD_DIR
from backend.services.ocr.document import get_image_metadata

UPLOAD_FOLDER = str(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ORIGINAL_UPLOAD_DIR, exist_ok=True)


def save_original_upload(filename: str, content: bytes) -> tuple[str, str, dict]:
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
    return os.path.join(upload_folder, filename)
