from io import BytesIO
import os
import unittest

from PIL import Image

from backend.services.ocr_service import adapt_paddleocr_result, save_original_upload


class OcrAdapterTests(unittest.TestCase):
    def test_adapter_keeps_source_pixel_coordinates_and_required_fields(self):
        item = adapt_paddleocr_result(
            {
                "rec_texts": ["力越大速度越快"],
                "rec_scores": [0.98],
                "rec_boxes": [[120, 500, 500, 560]],
            },
            0,
            2000,
            3000,
        )

        self.assertEqual(
            item,
            {
                "id": 1,
                "text": "力越大速度越快",
                "confidence": 0.98,
                "bbox": {"x": 120.0, "y": 500.0, "width": 380.0, "height": 60.0},
            },
        )

    def test_adapter_falls_back_to_dt_polys(self):
        item = adapt_paddleocr_result(
            {
                "rec_texts": ["答案"],
                "rec_scores": [0.91],
                "dt_polys": [[[10, 20], [80, 20], [80, 50], [10, 50]]],
            },
            0,
            100,
            100,
        )

        self.assertEqual(item["bbox"], {"x": 10.0, "y": 20.0, "width": 70.0, "height": 30.0})

    def test_save_original_upload_keeps_exact_bytes_and_source_metadata(self):
        source = BytesIO()
        Image.new("RGB", (37, 53), "white").save(source, format="PNG")
        content = source.getvalue()

        relative_path, filepath, metadata = save_original_upload("answer.png", content)
        try:
            with open(filepath, "rb") as saved_file:
                self.assertEqual(saved_file.read(), content)
            self.assertTrue(relative_path.startswith("original/"))
            self.assertEqual(metadata["original_width"], 37)
            self.assertEqual(metadata["original_height"], 53)
            self.assertEqual(metadata["format"], "png")
            self.assertEqual(metadata["file_path"], relative_path)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == "__main__":
    unittest.main()
