"""集中管理项目路径与环境配置，其他模块一律从这里导入。"""
import os
from pathlib import Path

from dotenv import load_dotenv

# config.py -> core -> backend -> project root
BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"                        # JSON 数据文件（用户、作业等）
STATIC_DIR = BASE_DIR / "static"                    # 后端静态资源
UPLOAD_DIR = BASE_DIR / "uploads"                   # 上传文件根目录
ORIGINAL_UPLOAD_DIR = UPLOAD_DIR / "original"       # 学生作业原图（保留原始字节）
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"  # 前端构建产物（生产模式托管）

# 会话签名密钥：生产环境务必通过环境变量覆盖默认值
SESSION_SECRET_KEY = os.getenv(
    "SESSION_SECRET_KEY", "ocr-app-secret-key-change-in-production"
)
