import json
import unittest

from backend.services.model_service import _parse_review


class ReviewCoordinateTests(unittest.TestCase):
    def setUp(self):
        self.ocr_document = {
            "coordinate_space": "source_pixel",
            "image_width": 1200,
            "image_height": 800,
            "items": [
                {
                    "id": "ocr-0",
                    "text": "2=1+1",
                    "box": {"x": 125, "y": 240, "width": 180, "height": 64},
                }
            ],
        }

    def test_review_uses_trusted_ocr_pixel_coordinates(self):
        model_response = json.dumps(
            {
                "score": 0,
                "comment": "这道题已经写出计算过程，但结果不符合本次评分标准。请重新核对题目规则，并按规则修正等式结果。",
                "error_items": [
                    {
                        "id": "ocr-0",
                        "text": "模型可以写错这段文本",
                        "box": {"x": 9999, "y": 9999, "width": 1, "height": 1},
                        "reason": "计算结果错误",
                    }
                ],
            },
            ensure_ascii=False,
        )

        review = _parse_review(model_response, self.ocr_document)

        self.assertEqual(
            review["error_boxes"],
            [
                {
                    "x": 125.0,
                    "y": 240.0,
                    "width": 180.0,
                    "height": 64.0,
                    "coordinate_space": "source_pixel",
                    "text": "2=1+1",
                    "reason": "计算结果错误",
                }
            ],
        )

    def test_review_ignores_unknown_ocr_ids(self):
        model_response = json.dumps(
            {
                "score": 80,
                "comment": "本次作业的主要步骤已经完成，现有答案表达比较清楚。请继续按照评分标准检查关键结果，避免遗漏必要过程。",
                "error_items": [
                    {
                        "id": "invented-id",
                        "text": "不存在",
                        "box": {"x": 0, "y": 0, "width": 10, "height": 10},
                        "reason": "虚构错误",
                    }
                ],
            },
            ensure_ascii=False,
        )

        review = _parse_review(model_response, self.ocr_document)

        self.assertEqual(review["error_boxes"], [])


if __name__ == "__main__":
    unittest.main()
