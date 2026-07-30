"""模型供应商配置。"""

import os
from dataclasses import dataclass

from backend.core import config as _config  # noqa: F401
from backend.exceptions.business import BusinessValidationException
from backend.exceptions.system import ModelConfigurationError


@dataclass(frozen=True)
class ModelSettings:
    provider: str
    label: str
    api_key: str
    model: str
    base_url: str = ""


MODEL_CONFIG = {
    "deepseek": {
        "label": "DeepSeek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_env": "DEEPSEEK_MODEL",
        "default_model": "deepseek-v4-flash",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "default_base_url": "https://api.deepseek.com",
    },
    "openai": {
        "label": "OpenAI",
        "api_key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-5.6",
    },
    "gemini": {
        "label": "Gemini",
        "api_key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-3.5-flash",
    },
}


def get_model_options() -> list[dict]:
    options = []
    for provider, config in MODEL_CONFIG.items():
        model = os.getenv(config["model_env"], config["default_model"]).strip()
        options.append(
            {
                "id": provider,
                "label": config["label"],
                "model": model,
                "available": bool(os.getenv(config["api_key_env"], "").strip()),
            }
        )
    return options


def get_model_settings(provider: str) -> ModelSettings:
    config = MODEL_CONFIG.get(provider)
    if not config:
        raise BusinessValidationException("所选评分模型不受支持，请从列表中重新选择。")
    api_key = os.getenv(config["api_key_env"], "").strip()
    if not api_key:
        raise ModelConfigurationError(
            f"未配置 {config['api_key_env']}，请先在服务端 .env 中填写该模型的 API Key。"
        )
    model = os.getenv(config["model_env"], config["default_model"]).strip()
    if not model:
        raise ModelConfigurationError(
            f"未配置 {config['model_env']}，请先在服务端 .env 中指定模型名称。"
        )
    base_url_env = config.get("base_url_env")
    base_url = (
        os.getenv(base_url_env, config.get("default_base_url", "")).rstrip("/")
        if base_url_env
        else ""
    )
    return ModelSettings(
        provider=provider,
        label=config["label"],
        api_key=api_key,
        model=model,
        base_url=base_url,
    )
