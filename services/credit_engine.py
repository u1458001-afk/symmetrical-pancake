"""修課紀錄正規化、重修追蹤與學分缺口計算。"""
import re
import unicodedata
from collections import defaultdict


class InputError(ValueError):
    """使用者輸入不符合預期時的錯誤。"""


PASS_STATUSES = {"通過", "及格", "抵免", "通過(抵免)", "已通過", "pass", "passed"}
FAIL_STATUSES = {"不及格", "未通過", "未過", "退選", "停修", "零分", "0", "fail", "failed"}
IN_PROGRESS_STATUSES = {"修課中", "進行中", "待評分", "in progress"}


def _credits(value, field):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise InputError(f"{field} 必須是數字。")
    if number < 0 or number > 30:
        raise InputError(f"{field} 必須介於 0 到 30。")
    return int(number) if number.is_integer() else number


def _required(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() in {"true", "1", "yes", "是", "必修"}


def normalize_courses(courses):
    if not isinstance(courses, list):
        raise InputError("課程資料必須是陣列。")
    if len(courses) > 500:
        raise InputError("單次最多匯入 500 門課程。")
    normalized = []
    for index, item in enumerate(courses, start=1):
        if not isinstance(item, dict):
            raise InputError(f"第 {index} 筆課程資料必須是物件。")
        name = str(item.get("name", item.get("課程名稱", item.get("課程", "")))).strip()
        if not name:
            raise InputError(f"第 {index} 筆課程資料缺少課程名稱。")
        score_value = item.get("score", item.get("grade", item.get("成績")))
        score = None
        if score_value not in (None, ""):
            try:
                score = float(score_value)
            except (TypeError, ValueError):
                raise InputError(f"第 {index} 筆成績必須是數字。")
            if score < 0 or score > 100:
                raise InputError(f"第 {index} 筆成績必須介於 0 到 100。")
        status = str(item.get("status", item.get("狀態", "通過"))).strip()
        category = str(item.get("category", item.get("類別", item.get("學分類別", "跨領域／自由選修")))).strip()
        if not category:
            category = "跨領域／自由選修"
        normalized.append({
            "code": str(item.get("code", item.get("課號", ""))).strip(),
            "name": name,
            "credits": _credits(item.get("credits", item.get("學分", 0)), f"第 {index} 筆學分"),
            "category": category,
            "status": status,
            "score": score,
            "semester": str(item.get("semester", item.get("學期", ""))).strip(),
            "required": _required(item.get("required", item.get("必修", False))),
        })
    return normalized


def _identity_text(value):
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return re.sub(r"[\s\W_]+", "", normalized, flags=re.UNICODE)


def _outcome(course):
    status = course["status"].casefold().strip()
    if status in IN_PROGRESS_STATUSES:
        return "修課中"
    if status in FAIL_STATUSES or (course["score"] is not None and course["score"] < 60):
        return "未通過"
    if status in PASS_STATUSES or (course["score"] is not None and course["score"] >= 60):
        return "通過"
    raise InputError(f"「{course['name']}」的狀態「{course['status']}」無法辨識；請填通過、不及格或修課中。")


def _course_groups(records):
    parents = list(range(len(records)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    aliases = {}
    for index, course in enumerate(records):
        identity_parts = []
        code = _identity_text(course["code"])
        name = _identity_text(course["name"])
        if code:
            identity_parts.append(("code", code))
        if name:
            identity_parts.append(("name", name))
        for part in identity_parts:
            if part in aliases:
                union(index, aliases[part])
            else:
                aliases[part] = index
    groups = defaultdict(list)
    for index, course in enumerate(records):
        groups[find(index)].append(course)
    return list(groups.values())


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
    for course in records:
        course["outcome"] = _outcome(course)
        course["earned_credits"] = course["credits"] if course["outcome"] == "通過" else 0
    grouped = _course_groups(records)
    passed_courses = []
    failed_courses = []
    in_progress_courses = []
    retake_history = []

    for attempts in grouped:
        passed = [course for course in attempts if course["outcome"] == "通過"]
        failed = [course for course in attempts if course["outcome"] == "未通過"]
        active = [course for course in attempts if course["outcome"] == "修課中"]
        representative = (passed or failed or active)[-1]
        history = {
            **representative,
            "attempt_count": len(attempts),
            "resolved": bool(passed),
            "attempts": attempts,
            "outcome": "已通過重修" if len(attempts) > 1 and passed else representative["outcome"],
        }
        for attempt in attempts:
            attempt["attempt_count"] = len(attempts)
            attempt["retake_resolved"] = bool(passed)
        if len(attempts) > 1:
            retake_history.append(history)
        if passed:
            # 同名或同課號的所有通過紀錄只採一次，以學分較高的通過紀錄計算。
            passed_courses.append(max(passed, key=lambda course: course["credits"]))
        elif failed:
            failed_courses.append(history)
        if active:
            in_progress_courses.append(history)

    earned_by_category = defaultdict(float)
    earned_total = 0.0
    for course in passed_courses:
        earned_total += course["credits"]
        earned_by_category[course["category"]] += course["credits"]
    category_results = {}
    for category, required in clean_requirements.items():
        earned = earned_total if category == "總學分" else earned_by_category.get(category, 0)
        category_results[category] = {
            "required": required,
            "earned": earned,
            "gap": max(0, required - earned),
            "surplus": max(0, earned - required),
        }
    return {
        "categories": category_results,
        "earned_total": earned_total,
        "failed_courses": failed_courses,
        "in_progress_courses": in_progress_courses,
        "retake_history": retake_history,
        "course_records": records,
        "passed_courses": passed_courses,
        "counted_course_count": len(passed_courses),
    }
