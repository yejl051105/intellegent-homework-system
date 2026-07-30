"""模型结构化输出约束。"""

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "comment": {"type": "string"},
        "wrong_answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "reason": {"type": "string"},
                    "deduction": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["id", "reason", "deduction"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["score", "comment", "wrong_answers"],
    "additionalProperties": False,
}

GEMINI_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "comment": {"type": "string"},
        "wrong_answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "reason": {"type": "string"},
                    "deduction": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["id", "reason", "deduction"],
            },
        },
    },
    "required": ["score", "comment", "wrong_answers"],
}
