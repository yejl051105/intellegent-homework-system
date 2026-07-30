"""模型评分工作流编排。"""

from backend.exceptions.business import BusinessValidationException
from backend.services.model.config import ModelSettings
from backend.services.model.prompts import build_prompts
from backend.services.model.providers import (
    generate_with_deepseek,
    generate_with_gemini,
    generate_with_openai,
)
from backend.services.model.review import parse_review


async def generate_homework_review(
    settings: ModelSettings,
    title: str,
    criteria_text: str,
    ocr_document: dict,
) -> dict:
    system_prompt, user_prompt = build_prompts(title, criteria_text, ocr_document)
    generators = {
        "deepseek": generate_with_deepseek,
        "openai": generate_with_openai,
        "gemini": generate_with_gemini,
    }
    generator = generators.get(settings.provider)
    if not generator:
        raise BusinessValidationException("所选评分模型不受支持，请从列表中重新选择。")
    content = await generator(settings, system_prompt, user_prompt)
    return parse_review(content, ocr_document)
