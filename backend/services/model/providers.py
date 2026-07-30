"""OpenAI、DeepSeek、Gemini HTTP 调用适配器。"""

import httpx

from backend.exceptions.system import ModelResponseError
from backend.services.model.config import ModelSettings
from backend.services.model.schemas import GEMINI_REVIEW_SCHEMA, REVIEW_SCHEMA


async def generate_with_openai(
    settings: ModelSettings, system_prompt: str, user_prompt: str
) -> str:
    request_body = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "homework_review",
                "schema": REVIEW_SCHEMA,
                "strict": True,
            },
        },
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=10.0)
        ) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPError as exc:
        raise ModelResponseError(
            "OpenAI 请求失败，请检查 API Key、网络和模型配置后重试。"
        ) from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ModelResponseError("OpenAI 返回内容不完整，请重新生成。") from exc


async def generate_with_deepseek(
    settings: ModelSettings, system_prompt: str, user_prompt: str
) -> str:
    request_body = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=10.0)
        ) as client:
            response = await client.post(
                f"{settings.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPError as exc:
        raise ModelResponseError(
            "DeepSeek 请求失败，请检查 API Key、网络和模型配置后重试。"
        ) from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ModelResponseError("DeepSeek 返回内容不完整，请重新生成。") from exc


async def generate_with_gemini(
    settings: ModelSettings, system_prompt: str, user_prompt: str
) -> str:
    request_body = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": GEMINI_REVIEW_SCHEMA,
        },
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=10.0)
        ) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{settings.model}:generateContent",
                headers={
                    "x-goog-api-key": settings.api_key,
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except httpx.HTTPError as exc:
        raise ModelResponseError(
            "Gemini 请求失败，请检查 API Key、网络和模型配置后重试。"
        ) from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ModelResponseError("Gemini 返回内容不完整，请重新生成。") from exc
