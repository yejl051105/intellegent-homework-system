"""兼容入口：模型实现位于 backend.services.model 包。"""

from backend.exceptions.system import ModelConfigurationError, ModelResponseError
from backend.services.model import (
    ModelSettings,
    generate_homework_review,
    get_model_options,
    get_model_settings,
    parse_review,
)

# 兼容现有测试与内部调用；新代码优先使用 parse_review。
_parse_review = parse_review

__all__ = [
    "ModelSettings",
    "ModelConfigurationError",
    "ModelResponseError",
    "get_model_options",
    "get_model_settings",
    "generate_homework_review",
]
