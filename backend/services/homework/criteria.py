"""评分标准 JSON 数据访问。"""

from datetime import datetime

from backend.services.homework.storage import CRITERIA_FILE, read_json, write_json


def get_criteria():
    return read_json(CRITERIA_FILE)


def create_criteria(
    title: str,
    filename: str = "",
    content: str = "",
    source_type: str | None = None,
):
    items = read_json(CRITERIA_FILE)
    criterion = {
        "id": max((item["id"] for item in items), default=0) + 1,
        "title": title,
        "filename": filename,
        "content": content,
        "source_type": source_type or ("text" if content else "file"),
        "created_at": datetime.now().isoformat(),
    }
    items.append(criterion)
    write_json(CRITERIA_FILE, items)
    return criterion


def delete_criteria(criteria_id: int):
    items = [
        item for item in read_json(CRITERIA_FILE) if item["id"] != criteria_id
    ]
    write_json(CRITERIA_FILE, items)
