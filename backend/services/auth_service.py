import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def _load_users():
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def authenticate(username: str, password: str):
    users = _load_users()
    for u in users:
        if u["username"] == username and u["password"] == password:
            return {"id": u["id"], "username": u["username"], "role": u["role"], "name": u["name"]}
    return None
