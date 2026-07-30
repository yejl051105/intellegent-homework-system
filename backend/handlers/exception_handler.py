import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from backend.exceptions.base import BaseAppException
from backend.exceptions.system import SystemException
from backend.utils.response import fail

logger = logging.getLogger(__name__)


def _detail_to_message(detail: Any) -> str:
    """HTTPException.detail 允许任意 JSON 值，统一响应的 message 则固定为字符串。"""
    if isinstance(detail, str):
        return detail
    if detail is None:
        return "请求失败"
    return str(detail)


async def base_app_exception_handler(request: Request, exc: BaseAppException):
    return fail(code=exc.code, message=exc.message, status_code=exc.http_status)


async def system_exception_handler(request: Request, exc: SystemException):
    logger.error(
        "系统异常: %s",
        exc.log_message,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return fail(code=exc.code, message=exc.message, status_code=exc.http_status)


async def http_exception_handler(request: Request, exc: HTTPException):
    return fail(
        code=exc.status_code,
        message=_detail_to_message(exc.detail),
        status_code=exc.status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return fail(code=422, message="请求参数校验失败", status_code=422)


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获的异常: %s", exc)
    return fail(code=50000, message="服务器内部错误", status_code=500)


def register_exception_handlers(app: FastAPI) -> None:
    """集中注册应用异常处理器，保证每个 app factory 实例行为一致。"""
    app.add_exception_handler(SystemException, system_exception_handler)
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
