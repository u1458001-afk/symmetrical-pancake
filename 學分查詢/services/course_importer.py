"""解析 JSON、CSV、簡易文字課程資料並讀取選填 HTTPS 來源。"""
import csv
import ipaddress
import io
import json
import re
import socket
from urllib.parse import urlparse

import requests

from config import MAX_IMPORT_BYTES, MAX_COURSES, REQUEST_TIMEOUT
from services.credit_engine import InputError, normalize_courses


FIELD_ALIASES = {
    "課程名稱": "name", "名稱": "name", "課程": "name", "name": "name",
    "課號": "code", "課程代碼": "code", "code": "code",
    "學分": "credits", "credits": "credits",
    "類別": "category", "學分類別": "category", "category": "category",
    "狀態": "status", "status": "status",
    "學期": "semester", "semester": "semester",
    "成績": "score", "score": "score", "grade": "score",
    "必修": "required", "required": "required",
}


def _map_row(row):
    return {FIELD_ALIASES.get(str(key).strip().casefold(), str(key).strip()): value for key, value in row.items()}


def _parse_text(content):
    rows = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            columns = [part.strip() for part in line.split("|")]
        elif "\t" in line:
            columns = [part.strip() for part in line.split("\t")]
        else:
            columns = [part.strip() for part in re.split(r",|，|\s{2,}", line)]
        columns = [part for part in columns if part]
        if len(columns) < 3:
            raise InputError(f"簡易文字第 {line_number} 行需包含課名、學分與類別，可用 | 或 Tab 分隔。")
        if columns[0].casefold() in {"code", "課號"}:
            continue
        if len(columns) >= 4 and _is_number(columns[2]):
            row = {"code": columns[0], "name": columns[1], "credits": columns[2], "category": columns[3]}
            if len(columns) >= 5:
                row["required"] = columns[4]
            if len(columns) >= 6:
                row["semester"] = columns[5]
        elif _is_number(columns[1]):
            row = {"name": columns[0], "credits": columns[1], "category": columns[2]}
            if len(columns) >= 4:
                row["status"] = columns[3]
            if len(columns) >= 5:
                row["code"] = columns[4]
        else:
            raise InputError(f"簡易文字第 {line_number} 行找不到學分數字，請確認欄位順序。")
        rows.append(row)
    return rows


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


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
        if content.lstrip().startswith(("[", "{")):
            chosen = "json"
        elif any(marker in content.splitlines()[0] for marker in ("課號", "課程名稱", "credits", "name", "名稱")):
            chosen = "csv"
        else:
            chosen = "text"
    try:
        if chosen == "json":
            raw = json.loads(content)
            if isinstance(raw, dict):
                raw = raw.get("courses", raw.get("課程", []))
        elif chosen == "csv":
            raw = [_map_row(row) for row in csv.DictReader(io.StringIO(content))]
        elif chosen in {"text", "txt"}:
            raw = _parse_text(content)
        else:
            raise InputError("支援的格式為 JSON、CSV 或簡易文字。")
    except (json.JSONDecodeError, csv.Error) as error:
        raise InputError(f"資料格式無法解析：{error}")
    if not isinstance(raw, list):
        raise InputError("JSON 頂層需為課程陣列，或包含 courses 陣列。")
    courses = normalize_courses([_map_row(row) if isinstance(row, dict) else row for row in raw])
    if len(courses) > MAX_COURSES:
        raise InputError("課程數量超過 500 門。")
    return courses


def fetch_courses(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise InputError("外部課程網址僅接受 HTTPS。")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise InputError("外部課程網址不可包含帳密，且僅接受 HTTPS 標準連接埠。")
    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname.endswith((".localhost", ".local", ".internal")) or hostname in {"localhost", "metadata.google.internal"}:
        raise InputError("外部課程網址必須指向公開網站。")
    try:
        try:
            addresses = [ipaddress.ip_address(hostname)]
        except ValueError:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)]
    except (OSError, ValueError, IndexError):
        raise InputError("無法解析外部課程網址的主機名稱。")
    if not addresses or any(not address.is_global for address in addresses):
        raise InputError("外部課程網址必須解析至公開網路位址。")
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "NUU-Credit-Planner/1.0", "Accept": "application/json, text/csv"},
            allow_redirects=False,
        )
        response.raise_for_status()
        if not 200 <= response.status_code < 300:
            raise InputError("外部課程來源未回傳成功結果，請檢查來源網址。")
    except InputError:
        raise
    except requests.Timeout:
        raise InputError("讀取外部課程來源逾時，請稍後重試或改用匯入檔案。")
    except requests.RequestException:
        raise InputError("無法取得外部課程資料，請確認網址與來源服務狀態。")
    if len(response.content) > MAX_IMPORT_BYTES:
        raise InputError("外部課程資料超過 1 MB。")
    content_type = response.headers.get("Content-Type", "").lower()
    if "json" in content_type or parsed.path.lower().endswith(".json"):
        fmt = "json"
    elif "csv" in content_type or parsed.path.lower().endswith(".csv"):
        fmt = "csv"
    else:
        fmt = "text"
    return import_courses(response.content, fmt)
