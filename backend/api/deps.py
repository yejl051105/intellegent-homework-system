from fastapi import Request

from backend.exceptions.business import NotLoginException, PermissionDeniedException


def get_user(request: Request):
    return request.session.get("user")


def require_user(request: Request, role: str | None = None):
    user = get_user(request)
    if not user:
        raise NotLoginException()
    if role and user["role"] != role:
        raise PermissionDeniedException()
    return user
