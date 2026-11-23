"""修課紀錄正規化與學分缺口計算。"""
from collections import defaultdict


class InputError(ValueError):
    """使用者輸入不符合預期時的錯誤。"""


PASS_STATUSES = {"通過", "及格", "通過(抵免)", "抵免", "pass", "passed", "已通過"}
FAIL_STATUSES = {"不及格", "未通過", "未過", "退選", "停修", "fail", "failed", "未達標"}
IN_PROGRESS_STATUSES = {"修課中", "進行中", "待評分", "in progress"}


def _credits(value, field):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise InputError(f"{field} 必須是數字。")
    if result < 0 or result > 30:
        raise InputError(f"{field} 必須介於 0 到 30。")
    return int(result) if result.is_integer() else result


def normalize_courses(courses):
    if not isinstance(courses, list):
        raise InputError("修課紀錄必須是課程陣列。")
    if len(courses) > 500:
        raise InputError("單次最多匯入 500 門課程。")
    normalized = []
    for index, item in enumerate(courses, start=1):
        if not isinstance(item, dict):
            raise InputError(f"第 {index} 筆修課紀錄必須是物件。")
        name = str(item.get("name", item.get("課程名稱", ""))).strip()
        if not name:
            raise InputError(f"第 {index} 筆修課紀錄缺少課程名稱。")
        status = str(item.get("status", item.get("狀態", "通過"))).strip()
        category = str(item.get("category", item.get("類別", "自由選修"))).strip() or "自由選修"
        required_value = item.get("required", item.get("必修", False))
        required = required_value if isinstance(required_value, bool) else str(required_value).strip().casefold() in {"true", "1", "yes", "是", "必修"}
        normalized.append({
            "code": str(item.get("code", item.get("課號", ""))).strip(),
            "name": name,
            "credits": _credits(item.get("credits", item.get("學分", 0)), f"第 {index} 筆學分"),
            "category": category,
            "status": status,
            "semester": str(item.get("semester", item.get("學期", ""))).strip(),
            "required": required,
        })
    return normalized


def calculate_credits(requirements, courses):
    if not isinstance(requirements, dict) or not requirements:
        raise InputError("請輸入至少一個學分門檻。")
    clean_requirements = {}
    for key, value in requirements.items():
        category = str(key).strip()
        if not category:
            raise InputError("學分類別不可空白。")
        clean_requirements[category] = _credits(value, f"「{category}」門檻")
    records = normalize_courses(courses)
    # 同一課號（或無課號時的課名）只計入一次，避免跨學期重修重複累計。
    attempts = {}
    failed = []
    in_progress = []
    for course in records:
        status_key = course["status"].casefold()
        identity = course["code"] or course["name"]
        if status_key in FAIL_STATUSES:
            failed.append(course)
            continue
        if status_key in IN_PROGRESS_STATUSES:
            in_progress.append(course)
            continue
        if status_key not in PASS_STATUSES:
            raise InputError(f"「{course['name']}」的狀態「{course['status']}」無法辨識；請填通過、不及格或修課中。")
        previous = attempts.get(identity)
        if previous is None or course["credits"] > previous["credits"]:
            attempts[identity] = course

    earned_by_category = defaultdict(float)
    earned_total = 0.0
    for course in attempts.values():
        earned_total += course["credits"]
        earned_by_category[course["category"]] += course["credits"]
    category_results = {}
    for category, required in clean_requirements.items():
        if category == "總學分":
            earned = earned_total
        elif category == "必修" and "必修" not in earned_by_category:
            earned = earned_by_category.get("必修", 0)
        else:
            earned = earned_by_category.get(category, 0)
        category_results[category] = {
            "required": required, "earned": earned,
            "gap": max(0, required - earned),
            "surplus": max(0, earned - required),
        }
    return {
        "categories": category_results,
        "earned_total": earned_total,
        "failed_courses": failed,
        "in_progress_courses": in_progress,
        "passed_courses": list(attempts.values()),
        "counted_course_count": len(attempts),
    }
