"""优秀作业展示记录的数据访问与关联清理。"""

from datetime import datetime

from backend.services.homework.storage import EXEMPLARY_FILE, read_json, write_json


def get_exemplary():
    return read_json(EXEMPLARY_FILE)


def create_exemplary(title: str, filename: str, description: str = ""):
    items = read_json(EXEMPLARY_FILE)
    exemplary = {
        "id": max((item["id"] for item in items), default=0) + 1,
        "title": title,
        "filename": filename,
        "description": description,
        "created_at": datetime.now().isoformat(),
    }
    items.append(exemplary)
    write_json(EXEMPLARY_FILE, items)
    return exemplary


def delete_exemplary(exemplary_id: int):
    items = [
        item for item in read_json(EXEMPLARY_FILE) if item["id"] != exemplary_id
    ]
    write_json(EXEMPLARY_FILE, items)


def remove_related_exemplary(homework: dict):
    items = read_json(EXEMPLARY_FILE)
    prefix = f"学生：{homework.get('student_name', '')}"
    removed = [
        item
        for item in items
        if item.get("title") == homework.get("title")
        and item.get("description", "").startswith(prefix)
    ]
    if removed:
        removed_ids = {item["id"] for item in removed}
        write_json(
            EXEMPLARY_FILE,
            [item for item in items if item["id"] not in removed_ids],
        )
    return removed
