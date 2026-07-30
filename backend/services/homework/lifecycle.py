"""角色级软删除、恢复与磁盘清理。"""

from datetime import datetime

from backend.core.config import UPLOAD_DIR
from backend.services.homework.exemplary import remove_related_exemplary
from backend.services.homework.repository import migrate_delete_state, role_flag
from backend.services.homework.storage import HOMEWORKS_FILE, read_json, write_json


def delete_homework(homework_id: int, role: str):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        migrate_delete_state(homework)
        if (
            homework["id"] == homework_id
            and not role_flag(homework, role, "deleted")
            and not role_flag(homework, role, "removed")
        ):
            homework[f"{role}_deleted"] = True
            homework[f"{role}_deleted_at"] = datetime.now().isoformat()
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def restore_homework(homework_id: int, role: str):
    items = read_json(HOMEWORKS_FILE)
    for homework in items:
        migrate_delete_state(homework)
        if (
            homework["id"] == homework_id
            and role_flag(homework, role, "deleted")
            and not role_flag(homework, role, "removed")
        ):
            homework[f"{role}_deleted"] = False
            homework[f"{role}_deleted_at"] = None
            write_json(HOMEWORKS_FILE, items)
            return homework
    return None


def permanently_delete_homework(homework_id: int, role: str):
    items = read_json(HOMEWORKS_FILE)
    for index, homework in enumerate(items):
        migrate_delete_state(homework)
        if (
            homework["id"] == homework_id
            and role_flag(homework, role, "deleted")
            and not role_flag(homework, role, "removed")
        ):
            homework[f"{role}_removed"] = True
            fully_removed = role_flag(
                homework, "student", "removed"
            ) and role_flag(homework, "teacher", "removed")
            deleted = items.pop(index) if fully_removed else homework
            write_json(HOMEWORKS_FILE, items)
            return deleted, fully_removed
    return None, False


def remove_homework_files(homework: dict):
    filenames = [homework.get("filename", "")]
    filenames.extend(
        item.get("filename", "") for item in remove_related_exemplary(homework)
    )
    for filename in filenames:
        if filename:
            path = UPLOAD_DIR / filename
            if path.is_file():
                path.unlink()
