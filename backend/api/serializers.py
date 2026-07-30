"""按角色裁剪返回给前端的作业字段。

作业记录中同时保存了「AI 草稿」（ai_ 前缀字段）和「教师确认后的结果」
（score / comment / error_boxes）。学生只能看到教师确认后的内容，
所以返回给学生端之前必须把 AI 草稿字段过滤掉。
"""


def student_payload(homework: dict):
    """学生端视图：去掉所有 ai_ 前缀字段和复核状态，未复核的 AI 建议绝不外泄。"""
    return {
        key: value
        for key, value in homework.items()
        if not key.startswith("ai_") and key not in {"review_status", "reviewed_by"}
    }


def exemplary_payload(homework: dict):
    """优秀作业展示视图：只保留展示墙需要的已复核字段（白名单方式）。"""
    allowed_fields = {
        "id",
        "student_name",
        "title",
        "filename",
        "score",
        "comment",
        "is_exemplary",
        "submitted_at",
        "graded_at",
    }
    return {key: value for key, value in homework.items() if key in allowed_fields}
