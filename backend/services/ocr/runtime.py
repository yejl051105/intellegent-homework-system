"""PaddleOCR 模型实例及懒加载生命周期。"""

import os
from threading import Lock
from typing import Any

from PIL import Image


class LazyPaddleOCR:
    """首次执行识别时才加载模型，避免阻塞 FastAPI 启动。"""

    def __init__(self) -> None:
        self._instance: Any | None = None
        self._lock = Lock()

    def _get_instance(self) -> Any:
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    from paddleocr import PaddleOCR

                    self._instance = PaddleOCR(
                        lang="ch",
                        use_textline_orientation=True,
                    )
        return self._instance

    def predict(self, *args, **kwargs):
        return self._get_instance().predict(*args, **kwargs)


ocr = LazyPaddleOCR()

_formula_recognizer = None
_formula_pipeline = None


def get_formula_recognizer():
    global _formula_recognizer
    if _formula_recognizer is None:
        from paddleocr import FormulaRecognition

        _formula_recognizer = FormulaRecognition(model_name="PP-FormulaNet_plus-S")
    return _formula_recognizer


def get_formula_pipeline():
    global _formula_pipeline
    if _formula_pipeline is None:
        from paddleocr import FormulaRecognitionPipeline

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
        lines = []
        for item in ocr.predict(region_path):
            lines.extend(item.get("rec_texts", []))
        return "".join(lines)
    finally:
        if os.path.exists(region_path):
            os.remove(region_path)
