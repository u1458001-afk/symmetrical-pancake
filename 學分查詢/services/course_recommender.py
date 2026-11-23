"""依未過必修與類別缺口排序推薦課程並試算擬選結果。"""
from services.credit_engine import InputError, normalize_courses


def _course_keys(course):
    code = "".join(str(course.get("code", "")).casefold().split())
    name = "".join(str(course.get("name", "")).casefold().split())
    return {key for key in (code, name) if key}


def recommend_courses(course_pool, calculation, failed_courses=None, selected_codes=None, semester_limit=30):
    pool = normalize_courses([{**course, "status": "通過"} for course in course_pool])
    try:
        limit = float(semester_limit)
    except (TypeError, ValueError):
        raise InputError("本學期學分上限必須是數字。")
    if limit < 0 or limit > 30:
        raise InputError("本學期學分上限必須介於 0 到 30。")
    selected_codes = set(selected_codes or [])
    failed = failed_courses if failed_courses is not None else calculation.get("failed_courses", [])
    failed_keys = set().union(*(_course_keys(course) for course in failed)) if failed else set()
    failed_required_keys = set().union(*(_course_keys(course) for course in failed if course.get("required"))) if any(course.get("required") for course in failed) else set()
    gaps = {name: item["gap"] for name, item in calculation["categories"].items() if name != "總學分"}
    total_gap = calculation["categories"].get("總學分", {}).get("gap", 0)
    positive_gaps = {name: gap for name, gap in gaps.items() if gap > 0}
    largest_gap = max(positive_gaps.values(), default=0)
    largest_categories = {name for name, gap in positive_gaps.items() if gap == largest_gap}
    candidates = []

    for course in pool:
        key = course["code"] or course["name"]
        if key in selected_codes:
            continue
        is_failed = bool(_course_keys(course) & failed_keys)
        failed_required = bool(_course_keys(course) & failed_required_keys)
        category_gap = gaps.get(course["category"], 0)
        required = course["required"] or is_failed
        if category_gap <= 0 and total_gap <= 0 and not required:
            continue
        if is_failed and (course["required"] or failed_required):
            rank, reason = 0, "未過必修・建議優先重修"
        elif category_gap > 0 and course["category"] in largest_categories:
            rank, reason = 1, f"最大缺口類別・尚缺 {category_gap:g} 學分"
        elif category_gap > 0:
            rank, reason = 2, f"補足「{course['category']}」缺口"
        elif is_failed:
            rank, reason = 2, "未過科目・建議重修"
        elif required:
            rank, reason = 2, "必修課程"
        else:
            rank, reason = 3, "補足畢業總學分"
        course["recommendation_reason"] = reason
        course["priority"] = rank
        course["gap"] = category_gap
        candidates.append((rank, -category_gap, course["name"].casefold(), course))

    candidates.sort(key=lambda item: item[:3])
    recommendations = [item[3] for item in candidates]
    return {
        "recommendations": recommendations,
        "largest_gap_categories": sorted(largest_categories),
        "largest_category_gap": largest_gap,
        "selected_credits": 0,
        "semester_limit": limit,
    }


def simulate_selection(recommendations, selected_codes, calculation, semester_limit=30):
    selected_codes = set(selected_codes or [])
    normalized = normalize_courses([{**course, "status": "通過"} for course in recommendations])
    available = {course["code"] or course["name"]: course for course in normalized}
    if selected_codes - available.keys():
        raise InputError("擬選清單含有不存在的課程。")
    selected = [available[code] for code in selected_codes]
    credits = sum(course["credits"] for course in selected)
    try:
        limit = float(semester_limit)
    except (TypeError, ValueError):
        raise InputError("本學期學分上限必須是數字。")
    if limit < 0 or limit > 30:
        raise InputError("本學期學分上限必須介於 0 到 30。")
    selected_by_category = {}
    for course in selected:
        selected_by_category[course["category"]] = selected_by_category.get(course["category"], 0) + course["credits"]
    remaining = {
        category: max(0, item["gap"] - selected_by_category.get(category, 0))
        for category, item in calculation["categories"].items()
    }
    return {
        "selected_courses": selected,
        "selected_credits": credits,
        "within_limit": credits <= limit,
        "semester_limit": limit,
        "projected_total": float(calculation["earned_total"]) + credits,
        "remaining_gaps": remaining,
    }
