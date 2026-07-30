"""兼容入口：OCR 实现位于 backend.services.ocr 包。"""

from backend.services.ocr import (
    UPLOAD_FOLDER,
    adapt_paddleocr_result,
    crop_image,
    extract_text,
    extract_text_document,
    get_formula_pipeline,
    get_formula_recognizer,
    get_image_metadata,
    ocr,
    ocr_region,
    save_original_upload,
    save_upload,
)

__all__ = [name for name in globals() if not name.startswith("_")]
