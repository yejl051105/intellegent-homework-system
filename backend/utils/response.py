from typing import Any

from fastapi.responses import JSONResponse

from backend.schemas.response import ApiResponse


def success(data: Any = None, code: int = 0, message: str = "success") -> ApiResponse:
    """构造成功响应；业务代码只能通过这个函数返回正常结果。"""
    return ApiResponse(code=code, message=message, data=data)


def fail(code: int, message: str, status_code: int) -> JSONResponse:
    """构造错误响应，仅供全局异常处理器使用。"""
    return JSONResponse(
        content=ApiResponse(code=code, message=message, data=None).model_dump(mode="json"),
        status_code=status_code,
    )
