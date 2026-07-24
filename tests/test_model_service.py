import json
import unittest

from backend.services.model_service import ModelResponseError, _parse_review


class ReviewCoordinateTests(unittest.TestCase):
    def setUp(self):
        self.ocr_document = {
            "coordinate_space": "source_pixel",
            "image_width": 1200,
            "image_height": 800,
            "items": [
                {
                    "id": 1,
                    "text": "2=1+1",
                    "bbox": {"x": 125, "y": 240, "width": 180, "height": 64},
                }
            ],
        }

    def test_review_uses_trusted_ocr_pixel_coordinates(self):
        model_response = json.dumps(
            {
                "score": 0,
                "comment": "这道题已经写出计算过程，但结果不符合本次评分标准。请重新核对题目规则，并按规则修正等式结果。",
                "wrong_answers": [
                    {
                        "id": 1,
                        "reason": "计算结果错误",
                        "deduction": 10,
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
                    "ocr_id": 1,
                    "bbox": {
                        "x": 119.0,
                        "y": 234.0,
                        "width": 192.0,
                        "height": 76.0,
                    },
                    "coordinate_space": "source_pixel",
                    "text": "2=1+1",
                    "reason": "计算结果错误",
                    "deduction": 10,
                }
            ],
        )

    def test_review_ignores_unknown_ocr_ids(self):
        model_response = json.dumps(
            {
                "score": 80,
                "comment": "本次作业的主要步骤已经完成，现有答案表达比较清楚。请继续按照评分标准检查关键结果，避免遗漏必要过程。",
                "wrong_answers": [
                    {
                        "id": 999,
                        "reason": "虚构错误",
                        "deduction": 10,
                    }
                ],
            },
            ensure_ascii=False,
        )

        review = _parse_review(model_response, self.ocr_document)

        self.assertEqual(review["error_boxes"], [])

    def test_review_rejects_invalid_deduction(self):
        model_response = json.dumps(
            {
                "score": 80,
                "comment": "本次作业的主要步骤已经完成，现有答案表达比较清楚。请继续按照评分标准检查关键结果，避免遗漏必要过程。",
                "wrong_answers": [
                    {
                        "id": 1,
                        "reason": "计算结果错误",
                        "deduction": 0,
                    }
                ],
            },
            ensure_ascii=False,
        )

        with self.assertRaises(ModelResponseError):
            _parse_review(model_response, self.ocr_document)


if __name__ == "__main__":
    unittest.main()
