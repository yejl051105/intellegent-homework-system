from backend.services.homework.criteria import create_criteria, delete_criteria, get_criteria
from backend.services.homework.exemplary import (
    create_exemplary,
    delete_exemplary,
    get_exemplary,
    remove_related_exemplary,
)
from backend.services.homework.lifecycle import (
    delete_homework,
    permanently_delete_homework,
    remove_homework_files,
    restore_homework,
)
from backend.services.homework.repository import (
    create_homework,
    get_deleted_homeworks,
    get_homework,
    get_homeworks,
)
from backend.services.homework.review import (
    finalize_ai_review,
    grade_homework,
    reset_ai_review,
    save_ai_review,
    save_ocr_document,
    set_exemplary,
)

__all__ = [
    "get_homeworks",
    "get_deleted_homeworks",
    "get_homework",
    "create_homework",
    "grade_homework",
    "save_ocr_document",
    "save_ai_review",
    "finalize_ai_review",
    "reset_ai_review",
    "set_exemplary",
    "delete_homework",
    "restore_homework",
    "permanently_delete_homework",
    "remove_homework_files",
    "get_criteria",
    "create_criteria",
    "delete_criteria",
    "get_exemplary",
    "create_exemplary",
    "delete_exemplary",
    "remove_related_exemplary",
]
