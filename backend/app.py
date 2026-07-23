import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when running as script
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.services.ocr_service import BASE_DIR
from backend.routers import ocr, formula, combined, api

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware, secret_key="ocr-app-secret-key-change-in-production"
)

static_dir = Path(BASE_DIR) / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount(
    "/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads"
)

# Serve built Vue SPA in production
frontend_dist = Path(BASE_DIR) / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(frontend_dist / "assets")),
        name="spa_assets",
    )

app.include_router(ocr.router)
app.include_router(formula.router)
app.include_router(combined.router)
app.include_router(api.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if user:
        redirect = (
            "/student/dashboard" if user["role"] == "student" else "/teacher/dashboard"
        )
        return RedirectResponse(url=redirect, status_code=302)
    spa_index = Path(BASE_DIR) / "frontend" / "dist" / "index.html"
    if spa_index.exists():
        return HTMLResponse(spa_index.read_text(encoding="utf-8"))
    return RedirectResponse(url="/login", status_code=302)


@app.get("/{full_path:path}")
async def spa_fallback(request: Request, full_path: str):
    if (
        full_path.startswith("api/")
        or full_path.startswith("static/")
        or full_path.startswith("uploads/")
    ):
        return HTMLResponse("Not found", status_code=404)
    spa_index = Path(BASE_DIR) / "frontend" / "dist" / "index.html"
    if spa_index.exists():
        return HTMLResponse(spa_index.read_text(encoding="utf-8"))
    return HTMLResponse("Not found", status_code=404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=5001, reload=True)
