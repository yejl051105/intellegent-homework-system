"""应用入口：组装 FastAPI 实例（中间件、静态目录、路由、SPA 托管）。"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.api.router import api_router
from backend.core.config import (
    FRONTEND_DIST_DIR,
    SESSION_SECRET_KEY,
    STATIC_DIR,
    UPLOAD_DIR,
)
from backend.handlers.exception_handler import register_exception_handlers


def create_app() -> FastAPI:
    """app factory：便于测试时创建独立实例。"""
    app = FastAPI(title="智能作业批改系统")

    # 开发期放开全部来源；上线前应收紧为前端域名白名单
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # 生产模式直接托管 Vue 构建产物（开发时用 vite dev server + 代理，见 vite.config.js）
    if FRONTEND_DIST_DIR.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")),
            name="spa_assets",
        )

    app.include_router(api_router)

    register_exception_handlers(app)

    def _spa_index() -> HTMLResponse | None:
        """读取 SPA 入口页；前端尚未构建时返回 None。"""
        spa_index = FRONTEND_DIST_DIR / "index.html"
        if spa_index.exists():
            return HTMLResponse(spa_index.read_text(encoding="utf-8"))
        return None

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """首页：已登录按角色跳转对应工作台，未登录进 SPA 登录页。"""
        user = request.session.get("user")
        if user:
            redirect = (
                "/student/dashboard"
                if user["role"] == "student"
                else "/teacher/dashboard"
            )
            return RedirectResponse(url=redirect, status_code=302)
        response = _spa_index()
        if response:
            return response
        return RedirectResponse(url="/login", status_code=302)

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        """兜底路由：非 API/静态资源的路径都交给前端路由处理（history 模式刷新不 404）。"""
        if (
            full_path.startswith("api/")
            or full_path.startswith("static/")
            or full_path.startswith("uploads/")
        ):
            raise HTTPException(status_code=404, detail="Not found")
        response = _spa_index()
        if response:
            return response
        return HTMLResponse("Not found", status_code=404)

    return app


app = create_app()
