import json

from backend.core.config import DATA_DIR
from backend.exceptions.business import PasswordMismatchException, UserNotFoundException

USERS_FILE = DATA_DIR / "users.json"


def _load_users():
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def authenticate(username: str, password: str):
    users = _load_users()
    for u in users:
        if u["username"] == username:
            if u["password"] == password:
                return {"id": u["id"], "username": u["username"], "role": u["role"], "name": u["name"]}
            raise PasswordMismatchException()
    raise UserNotFoundException(f"用户 '{username}' 不存在")
