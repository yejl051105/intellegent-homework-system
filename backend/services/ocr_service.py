import os
from PIL import Image

from paddleocr import PaddleOCR, FormulaRecognition, FormulaRecognitionPipeline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    result = ocr.predict(filepath)
    lines = []
    for item in result:
        lines.extend(item.get("rec_texts", []))
    return "\n".join(line.strip() for line in lines if line.strip())


def save_upload(image, upload_folder: str) -> str:
    import uuid

    ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    return filepath
