import unittest

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from backend.api.routes import auth
from backend.exceptions import (
    BusinessException,
    DatabaseException,
    AuthException,
    OrderException,
    OrderNotFoundException,
    RedisException,
    SystemException,
    ThirdPartyServiceException,
    NotLoginException,
    UserException,
    UserNotFoundException,
)
from backend.handlers.exception_handler import register_exception_handlers


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    app.include_router(auth.router)
    register_exception_handlers(app)

    @app.get("/http-error")
    async def http_error():
        raise HTTPException(status_code=418, detail="HTTP 层异常")

    @app.get("/validated/{item_id}")
    async def validated(item_id: int):
        return {"item_id": item_id}

    @app.get("/unexpected")
    async def unexpected():
        raise RuntimeError("sensitive internal detail")

    @app.get("/system-error")
    async def system_error():
        raise RedisException("redis://:secret@localhost:6379/0")

    return app


class ExceptionHandlingTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_test_app(), raise_server_exceptions=False)

    def test_me_without_session_uses_business_code_and_http_status(self):
        response = self.client.get("/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"code": 10001, "message": "未登录", "data": None},
        )

    def test_me_with_session_uses_success_response(self):
        login_response = self.client.post(
            "/api/login",
            json={"username": "student1", "password": "123456"},
        )
        response = self.client.get("/me")

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], 0)
        self.assertEqual(response.json()["message"], "success")
        self.assertEqual(response.json()["data"]["username"], "student1")

    def test_http_exception_uses_unified_response(self):
        response = self.client.get("/http-error")

        self.assertEqual(response.status_code, 418)
        self.assertEqual(
            response.json(),
            {"code": 418, "message": "HTTP 层异常", "data": None},
        )

    def test_request_validation_error_uses_unified_response(self):
        response = self.client.get("/validated/not-an-integer")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {"code": 422, "message": "请求参数校验失败", "data": None},
        )

    def test_unknown_exception_hides_internal_detail(self):
        response = self.client.get("/unexpected")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"code": 50000, "message": "服务器内部错误", "data": None},
        )

    def test_system_exception_is_logged_and_sanitized(self):
        response = self.client.get("/system-error")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"code": 50001, "message": "缓存服务暂时不可用", "data": None},
        )
        self.assertNotIn("secret", response.text)

    def test_exception_hierarchy_separates_business_and_system(self):
        self.assertTrue(issubclass(UserNotFoundException, BusinessException))
        self.assertTrue(issubclass(UserNotFoundException, UserException))
        self.assertTrue(issubclass(NotLoginException, BusinessException))
        self.assertTrue(issubclass(NotLoginException, AuthException))
        self.assertTrue(issubclass(OrderNotFoundException, BusinessException))
        self.assertTrue(issubclass(OrderNotFoundException, OrderException))
        self.assertTrue(issubclass(RedisException, SystemException))
        self.assertTrue(issubclass(DatabaseException, SystemException))
        self.assertTrue(issubclass(ThirdPartyServiceException, SystemException))


if __name__ == "__main__":
    unittest.main()
