"""應用程式預設值與安全設定。"""
import os

DEFAULT_REQUIREMENTS = {
    "總學分": 128,
    "必修": 60,
    "通識": 28,
    "系選修": 24,
    "自由選修": 16,
}

# 僅供操作示範，並非聯大當學期官方開課資料。
DEMO_COURSES = [
    {"code": "DEMO-001", "name": "程式設計（一）", "credits": 3, "category": "必修", "required": True, "semester": "示範資料"},
    {"code": "DEMO-002", "name": "資料結構", "credits": 3, "category": "必修", "required": True, "semester": "示範資料"},
    {"code": "DEMO-003", "name": "工程倫理", "credits": 2, "category": "通識", "required": False, "semester": "示範資料"},
    {"code": "DEMO-004", "name": "台灣文化與社會", "credits": 2, "category": "通識", "required": False, "semester": "示範資料"},
    {"code": "DEMO-005", "name": "網頁應用程式", "credits": 3, "category": "系選修", "required": False, "semester": "示範資料"},
    {"code": "DEMO-006", "name": "資料視覺化", "credits": 3, "category": "自由選修", "required": False, "semester": "示範資料"},
]

REQUEST_TIMEOUT = float(os.getenv("COURSE_REQUEST_TIMEOUT", "8"))
MAX_IMPORT_BYTES = 1_000_000
MAX_COURSES = 500
MAX_CREDITS_PER_COURSE = 30
MAX_SEMESTER_CREDITS = 30
EXTERNAL_COURSE_URL = os.getenv("COURSE_SOURCE_URL", "").strip()
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "開發環境請設定正式金鑰")
