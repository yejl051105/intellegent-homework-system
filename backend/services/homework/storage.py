"""JSON 文件存储基础设施。"""

import json

from backend.core.config import DATA_DIR

HOMEWORKS_FILE = DATA_DIR / "homeworks.json"
CRITERIA_FILE = DATA_DIR / "criteria.json"
EXEMPLARY_FILE = DATA_DIR / "exemplary.json"


def read_json(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as source:
        return json.load(source)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
