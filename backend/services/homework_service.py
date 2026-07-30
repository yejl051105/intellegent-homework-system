"""兼容入口：作业领域实现位于 backend.services.homework 包。"""

from backend.services.homework import (
    create_criteria,
    create_exemplary,
    create_homework,
    delete_criteria,
    delete_exemplary,
    delete_homework,
    finalize_ai_review,
    get_criteria,
    get_deleted_homeworks,
    get_exemplary,
    get_homework,
    get_homeworks,
    grade_homework,
    permanently_delete_homework,
    remove_homework_files,
    remove_related_exemplary,
    reset_ai_review,
    restore_homework,
    save_ai_review,
    save_ocr_document,
    set_exemplary,
)

__all__ = [name for name in globals() if not name.startswith("_")]
