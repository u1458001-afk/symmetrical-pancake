"""課程清單匯入工具：文字、JSON、CSV 與選填外部 URL。"""
import csv
import io
import json
from urllib.parse import urlparse

import requests

from config import MAX_IMPORT_BYTES, MAX_COURSES, REQUEST_TIMEOUT
from services.credit_engine import InputError, normalize_courses


def import_courses(content, file_format="auto"):
    if isinstance(content, bytes):
        if len(content) > MAX_IMPORT_BYTES:
            raise InputError("匯入內容超過 1 MB。")
        try:
            content = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise InputError("檔案請使用 UTF-8 編碼。")
    if not isinstance(content, str) or not content.strip():
        raise InputError("請貼上或選擇非空白的課程資料。")
    if len(content.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise InputError("匯入內容超過 1 MB。")
    chosen = file_format.lower()
    if chosen == "auto":
        chosen = "json" if content.lstrip().startswith(("[", "{")) else "csv"
    try:
        if chosen == "json":
            raw = json.loads(content)
            if isinstance(raw, dict):
                raw = raw.get("courses", raw.get("課程", []))
        elif chosen == "csv":
            raw = list(csv.DictReader(io.StringIO(content)))
        else:
            raise InputError("支援的格式為 JSON 或 CSV。")
    except (json.JSONDecodeError, csv.Error) as error:
        raise InputError(f"資料格式無法解析：{error}")
    if not isinstance(raw, list):
        raise InputError("JSON 頂層需為課程陣列，或包含 courses 陣列。")
    aliases = {"課程名稱": "name", "名稱": "name", "課程": "name", "課號": "code", "學分": "credits",
               "類別": "category", "學分類別": "category", "狀態": "status", "學期": "semester", "必修": "required"}
    mapped = [{aliases.get(key, key): value for key, value in item.items()} if isinstance(item, dict) else item for item in raw]
    return normalize_courses(mapped)


def fetch_courses(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise InputError("外部課程網址僅接受 HTTPS。")
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"Accept": "application/json, text/csv"}, allow_redirects=False)
        response.raise_for_status()
        if not 200 <= response.status_code < 300:
            raise InputError("外部課程來源未回傳成功結果，請檢查來源網址。")
    except InputError:
        raise
    except requests.RequestException:
        raise InputError("無法取得外部課程資料，請確認網址、來源服務與網路狀態。")
    if len(response.content) > MAX_IMPORT_BYTES:
        raise InputError("外部課程資料超過 1 MB。")
    content_type = response.headers.get("Content-Type", "").lower()
    fmt = "json" if "json" in content_type or parsed.path.lower().endswith(".json") else "csv"
    courses = import_courses(response.content, fmt)
    if len(courses) > MAX_COURSES:
        raise InputError("課程數量超過上限。")
    return courses
