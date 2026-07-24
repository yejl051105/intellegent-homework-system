import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
HOMEWORKS_FILE = DATA_DIR / "homeworks.json"
CRITERIA_FILE = DATA_DIR / "criteria.json"
EXEMPLARY_FILE = DATA_DIR / "exemplary.json"


def _read_json(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Homeworks ──

def _role_flag(homework: dict, role: str, name: str) -> bool:
    """Read role-scoped state while treating legacy global deletions as deleted."""
    key = f"{role}_{name}"
    if key in homework:
        return bool(homework[key])
    return bool(homework.get("is_deleted", False)) if name == "deleted" else False


def _migrate_delete_state(homework: dict):
    """Expand records written before role-scoped deletion existed."""
    legacy_deleted = bool(homework.get("is_deleted", False))
    legacy_deleted_at = homework.get("deleted_at")
    for role in ("student", "teacher"):
        homework.setdefault(f"{role}_deleted", legacy_deleted)
        homework.setdefault(f"{role}_deleted_at", legacy_deleted_at if legacy_deleted else None)
        homework.setdefault(f"{role}_removed", False)


def get_homeworks(filters=None, include_deleted=False, role: str | None = None):
    items = _read_json(HOMEWORKS_FILE)
    if role:
        if include_deleted:
            items = [item for item in items if not _role_flag(item, role, "removed")]
        else:
            items = [
                item
                for item in items
                if not _role_flag(item, role, "deleted") and not _role_flag(item, role, "removed")
            ]
    elif not include_deleted:
        items = [i for i in items if not i.get("is_deleted", False)]
    if filters:
        for key, val in filters.items():
            items = [i for i in items if i.get(key) == val]
    return sorted(items, key=lambda x: x.get("submitted_at", ""), reverse=True)


def get_deleted_homeworks(role: str, filters=None):
    items = [
        item
        for item in _read_json(HOMEWORKS_FILE)
        if _role_flag(item, role, "deleted") and not _role_flag(item, role, "removed")
    ]
    if filters:
        for key, value in filters.items():
            items = [item for item in items if item.get(key) == value]
    return sorted(items, key=lambda x: x.get("submitted_at", ""), reverse=True)


def get_homework(homework_id: int, include_deleted=False, role: str | None = None):
    items = get_homeworks(include_deleted=include_deleted, role=role)
    for h in items:
        if h["id"] == homework_id:
            return h
    return None


def create_homework(student_id: int, student_name: str, title: str, filename: str, ocr_text: str = ""):
    items = _read_json(HOMEWORKS_FILE)
    new_id = max((h["id"] for h in items), default=0) + 1
    hw = {
        "id": new_id,
        "student_id": student_id,
        "student_name": student_name,
        "title": title,
        "filename": filename,
        "ocr_text": ocr_text or "",
        "ocr_document": None,
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
    items.append(hw)
    _write_json(HOMEWORKS_FILE, items)
    return hw


def grade_homework(homework_id: int, score: int, comment: str):
    items = _read_json(HOMEWORKS_FILE)
    for h in items:
        if h["id"] == homework_id:
            h["score"] = score
            h["comment"] = comment
            h["graded_at"] = datetime.now().isoformat()
            _write_json(HOMEWORKS_FILE, items)
            return h
    return None


def save_ocr_document(homework_id: int, document: dict):
    items = _read_json(HOMEWORKS_FILE)
    for h in items:
        if h["id"] == homework_id:
            h["ocr_document"] = document
            h["ocr_text"] = "\n".join(item["text"] for item in document.get("items", []))
            _write_json(HOMEWORKS_FILE, items)
            return h
    return None


def save_ai_review(homework_id: int, review: dict, model: str, criterion: dict):
    items = _read_json(HOMEWORKS_FILE)
    for h in items:
        if h["id"] == homework_id:
            # A new AI run replaces any previously confirmed result with a draft.
            h["score"] = None
            h["comment"] = ""
            h["error_boxes"] = []
            h["graded_at"] = None
            h["reviewed_by"] = None
            h["ai_score"] = review["score"]
            h["ai_comment"] = review["comment"]
            h["ai_rationale"] = ""
            h["ai_error_boxes"] = review["error_boxes"]
            h["ai_model"] = model
            h["ai_generated_at"] = datetime.now().isoformat()
            h["ai_criteria_id"] = criterion["id"]
            h["ai_criteria_title"] = criterion["title"]
            h["review_status"] = "ai_suggested"
            _write_json(HOMEWORKS_FILE, items)
            return h
    return None


def finalize_ai_review(homework_id: int, score: int, comment: str, error_boxes: list[dict], reviewer: dict):
    items = _read_json(HOMEWORKS_FILE)
    for h in items:
        if h["id"] == homework_id:
            h["score"] = score
            h["comment"] = comment
            h["error_boxes"] = error_boxes
            h["graded_at"] = datetime.now().isoformat()
            h["review_status"] = "confirmed"
            h["reviewed_by"] = {"id": reviewer["id"], "name": reviewer["name"]}
            _write_json(HOMEWORKS_FILE, items)
            return h
    return None


def reset_ai_review(homework_id: int):
    """Return a homework to the same review state it had immediately after upload."""
    items = _read_json(HOMEWORKS_FILE)
    for h in items:
        if h["id"] == homework_id:
            h["score"] = None
            h["comment"] = ""
            h["error_boxes"] = []
            h["graded_at"] = None
            h["ai_score"] = None
            h["ai_comment"] = ""
            h["ai_rationale"] = ""
            h["ai_error_boxes"] = []
            h["ai_model"] = ""
            h["ai_generated_at"] = None
            h["ai_criteria_id"] = None
            h["ai_criteria_title"] = ""
            h["review_status"] = "pending_ai"
            h["reviewed_by"] = None
            _write_json(HOMEWORKS_FILE, items)
            return h
    return None


def set_exemplary(homework_id: int, exemplary: bool = True):
    items = _read_json(HOMEWORKS_FILE)
    for h in items:
        if h["id"] == homework_id:
            h["is_exemplary"] = exemplary
            _write_json(HOMEWORKS_FILE, items)
            return h
    return None


def delete_homework(homework_id: int, role: str):
    items = _read_json(HOMEWORKS_FILE)
    for homework in items:
        _migrate_delete_state(homework)
        if homework["id"] == homework_id and not _role_flag(homework, role, "deleted") and not _role_flag(homework, role, "removed"):
            homework[f"{role}_deleted"] = True
            homework[f"{role}_deleted_at"] = datetime.now().isoformat()
            _write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def restore_homework(homework_id: int, role: str):
    items = _read_json(HOMEWORKS_FILE)
    for homework in items:
        _migrate_delete_state(homework)
        if homework["id"] == homework_id and _role_flag(homework, role, "deleted") and not _role_flag(homework, role, "removed"):
            homework[f"{role}_deleted"] = False
            homework[f"{role}_deleted_at"] = None
            _write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def permanently_delete_homework(homework_id: int, role: str):
    items = _read_json(HOMEWORKS_FILE)
    for index, homework in enumerate(items):
        _migrate_delete_state(homework)
        if homework["id"] == homework_id and _role_flag(homework, role, "deleted") and not _role_flag(homework, role, "removed"):
            homework[f"{role}_removed"] = True
            fully_removed = _role_flag(homework, "student", "removed") and _role_flag(homework, "teacher", "removed")
            deleted = items.pop(index) if fully_removed else homework
            _write_json(HOMEWORKS_FILE, items)
            return deleted, fully_removed
    return None, False


def remove_related_exemplary(homework: dict):
    """Remove legacy copied exemplary records when their source is permanently deleted."""
    items = _read_json(EXEMPLARY_FILE)
    prefix = f"学生：{homework.get('student_name', '')}"
    removed = [
        item
        for item in items
        if item.get("title") == homework.get("title")
        and item.get("description", "").startswith(prefix)
    ]
    if removed:
        removed_ids = {item["id"] for item in removed}
        _write_json(EXEMPLARY_FILE, [item for item in items if item["id"] not in removed_ids])
    return removed


# ── Criteria ──

def get_criteria():
    return _read_json(CRITERIA_FILE)


def create_criteria(title: str, filename: str = "", content: str = "", source_type: str | None = None):
    items = _read_json(CRITERIA_FILE)
    new_id = max((c["id"] for c in items), default=0) + 1
    c = {
        "id": new_id,
        "title": title,
        "filename": filename,
        "content": content,
        "source_type": source_type or ("text" if content else "file"),
        "created_at": datetime.now().isoformat(),
    }
    items.append(c)
    _write_json(CRITERIA_FILE, items)
    return c


def delete_criteria(criteria_id: int):
    items = _read_json(CRITERIA_FILE)
    items = [c for c in items if c["id"] != criteria_id]
    _write_json(CRITERIA_FILE, items)


# ── Exemplary uploads (standalone, not linked to homework) ──

def get_exemplary():
    return _read_json(EXEMPLARY_FILE)


def create_exemplary(title: str, filename: str, description: str = ""):
    items = _read_json(EXEMPLARY_FILE)
    new_id = max((e["id"] for e in items), default=0) + 1
    e = {
        "id": new_id,
        "title": title,
        "filename": filename,
        "description": description,
        "created_at": datetime.now().isoformat(),
    }
    items.append(e)
    _write_json(EXEMPLARY_FILE, items)
    return e


def delete_exemplary(exemplary_id: int):
    items = _read_json(EXEMPLARY_FILE)
    items = [e for e in items if e["id"] != exemplary_id]
    _write_json(EXEMPLARY_FILE, items)
