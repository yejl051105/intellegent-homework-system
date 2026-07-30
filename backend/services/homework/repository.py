"""作业查询与创建。"""

from datetime import datetime

from backend.services.homework.storage import HOMEWORKS_FILE, read_json, write_json


def role_flag(homework: dict, role: str, name: str) -> bool:
    key = f"{role}_{name}"
    if key in homework:
        return bool(homework[key])
    return bool(homework.get("is_deleted", False)) if name == "deleted" else False


def migrate_delete_state(homework: dict) -> None:
    legacy_deleted = bool(homework.get("is_deleted", False))
    legacy_deleted_at = homework.get("deleted_at")
    for role in ("student", "teacher"):
        homework.setdefault(f"{role}_deleted", legacy_deleted)
        homework.setdefault(
            f"{role}_deleted_at", legacy_deleted_at if legacy_deleted else None
        )
        homework.setdefault(f"{role}_removed", False)


def get_homeworks(filters=None, include_deleted=False, role: str | None = None):
    items = read_json(HOMEWORKS_FILE)
    if role:
        if include_deleted:
            items = [item for item in items if not role_flag(item, role, "removed")]
        else:
            items = [
                item
                for item in items
                if not role_flag(item, role, "deleted")
                and not role_flag(item, role, "removed")
            ]
    elif not include_deleted:
        items = [item for item in items if not item.get("is_deleted", False)]
    if filters:
        for key, value in filters.items():
            items = [item for item in items if item.get(key) == value]
    return sorted(items, key=lambda item: item.get("submitted_at", ""), reverse=True)


def get_deleted_homeworks(role: str, filters=None):
    items = [
        item
        for item in read_json(HOMEWORKS_FILE)
        if role_flag(item, role, "deleted") and not role_flag(item, role, "removed")
    ]
    if filters:
        for key, value in filters.items():
            items = [item for item in items if item.get(key) == value]
    return sorted(items, key=lambda item: item.get("submitted_at", ""), reverse=True)


def get_homework(homework_id: int, include_deleted=False, role: str | None = None):
    for homework in get_homeworks(include_deleted=include_deleted, role=role):
        if homework["id"] == homework_id:
            return homework
    return None


def create_homework(
    student_id: int,
    student_name: str,
    title: str,
    filename: str,
    ocr_document: dict | None = None,
    image_metadata: dict | None = None,
):
    items = read_json(HOMEWORKS_FILE)
    new_id = max((item["id"] for item in items), default=0) + 1
    ocr_document = ocr_document or {}
    image_metadata = image_metadata or ocr_document.get("image") or {}
    homework = {
        "id": new_id,
        "student_id": student_id,
        "student_name": student_name,
        "title": title,
        "filename": filename,
        "ocr_text": "\n".join(
            item.get("text", "") for item in ocr_document.get("items", [])
        ),
        "ocr_document": ocr_document or None,
        "image_metadata": image_metadata,
        "original_width": image_metadata.get("original_width"),
        "original_height": image_metadata.get("original_height"),
        "original_file_path": image_metadata.get("file_path", filename),
        "score": None,
        "comment": "",
        "is_exemplary": False,
        "student_deleted": False,
        "student_deleted_at": None,
        "student_removed": False,
        "teacher_deleted": False,
        "teacher_deleted_at": None,
        "teacher_removed": False,
        "submitted_at": datetime.now().isoformat(),
        "graded_at": None,
        "ai_score": None,
        "ai_comment": "",
        "ai_rationale": "",
        "ai_error_boxes": [],
        "error_boxes": [],
        "ai_model": "",
        "ai_generated_at": None,
        "ai_criteria_id": None,
        "ai_criteria_title": "",
        "review_status": "pending_ai",
        "reviewed_by": None,
    }
    items.append(homework)
    write_json(HOMEWORKS_FILE, items)
    return homework
