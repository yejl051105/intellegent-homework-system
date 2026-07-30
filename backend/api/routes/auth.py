from fastapi import APIRouter, Request

from backend.api.deps import get_user, require_user
from backend.exceptions.business import NotLoginException, PermissionDeniedException
from backend.schemas.response import ApiResponse
from backend.services.auth_service import authenticate
from backend.services.permission_service import get_route_permissions
from backend.utils.response import success

router = APIRouter(tags=["auth"])


@router.post("/api/login", response_model=ApiResponse)
async def api_login(request: Request):
    body = await request.json()
    user = authenticate(body.get("username", ""), body.get("password", ""))
    request.session["user"] = user
    return success(data=user)


@router.post("/api/logout", response_model=ApiResponse)
async def api_logout(request: Request):
    request.session.clear()
    return success(data={"ok": True})


# 兼容旧客户端使用的api include_in_schema=False表示不显示这个接口在自动生成的接口文档中
@router.get("/me", response_model=ApiResponse, include_in_schema=False)
@router.get("/api/me", response_model=ApiResponse)
async def api_me(request: Request):
    user = get_user(request)
    if not user:
        raise NotLoginException()
    return success(data=user)


@router.get("/api/routes", response_model=ApiResponse)
async def api_routes(request: Request):
    user = require_user(request)
    permissions = get_route_permissions(user)
    if not permissions:
        raise PermissionDeniedException("当前账号没有可用权限")
    return success(data=permissions)
