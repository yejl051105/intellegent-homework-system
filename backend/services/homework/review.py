"""作业评分与 AI 复核状态机。"""

from datetime import datetime

from backend.services.homework.storage import HOMEWORKS_FILE, read_json, write_json


def grade_homework(homework_id: int, score: int, comment: str):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        if homework["id"] == homework_id:
            homework["score"] = score
            homework["comment"] = comment
            homework["graded_at"] = datetime.now().isoformat()
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def save_ocr_document(homework_id: int, document: dict):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        if homework["id"] == homework_id:
            homework["ocr_document"] = document
            homework["ocr_text"] = "\n".join(
                item.get("text", "") for item in document.get("items", [])
            )
            image_metadata = document.get("image") or {}
            if image_metadata:
                homework["image_metadata"] = image_metadata
                homework["original_width"] = image_metadata.get("original_width")
                homework["original_height"] = image_metadata.get("original_height")
                homework["original_file_path"] = image_metadata.get(
                    "file_path", homework.get("filename", "")
                )
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def save_ai_review(homework_id: int, review: dict, model: str, criterion: dict):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        if homework["id"] == homework_id:
            homework["score"] = None
            homework["comment"] = ""
            homework["error_boxes"] = []
            homework["graded_at"] = None
            homework["reviewed_by"] = None
            homework["ai_score"] = review["score"]
            homework["ai_comment"] = review["comment"]
            homework["ai_rationale"] = ""
            homework["ai_error_boxes"] = review["error_boxes"]
            homework["ai_model"] = model
            homework["ai_generated_at"] = datetime.now().isoformat()
            homework["ai_criteria_id"] = criterion["id"]
            homework["ai_criteria_title"] = criterion["title"]
            homework["review_status"] = "ai_suggested"
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def finalize_ai_review(
    homework_id: int,
    score: int,
    comment: str,
    error_boxes: list[dict],
    reviewer: dict,
):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        if homework["id"] == homework_id:
            homework["score"] = score
            homework["comment"] = comment
            homework["error_boxes"] = error_boxes
            homework["graded_at"] = datetime.now().isoformat()
            homework["review_status"] = "confirmed"
            homework["reviewed_by"] = {
                "id": reviewer["id"],
                "name": reviewer["name"],
            }
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def reset_ai_review(homework_id: int):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        if homework["id"] == homework_id:
            homework.update(
                {
                    "score": None,
                    "comment": "",
                    "error_boxes": [],
                    "graded_at": None,
                    "ai_score": None,
                    "ai_comment": "",
                    "ai_rationale": "",
                    "ai_error_boxes": [],
                    "ai_model": "",
                    "ai_generated_at": None,
                    "ai_criteria_id": None,
                    "ai_criteria_title": "",
                    "review_status": "pending_ai",
                    "reviewed_by": None,
                }
            )
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def set_exemplary(homework_id: int, exemplary: bool = True):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        if homework["id"] == homework_id:
            homework["is_exemplary"] = exemplary
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None
