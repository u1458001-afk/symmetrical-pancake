"""依缺口和未過科目排序擬選清單。"""
from services.credit_engine import InputError, normalize_courses


def recommend_courses(course_pool, calculation, failed_courses=None, selected_codes=None, semester_limit=30):
    pool = normalize_courses([
        {**course, "status": "通過"} for course in course_pool
    ])
    limit = float(semester_limit)
    if limit < 0 or limit > 30:
        raise InputError("本學期學分上限必須介於 0 到 30。")
    selected_codes = set(selected_codes or [])
    failed_names = {course["name"] for course in (failed_courses or calculation.get("failed_courses", []))}
    gaps = {name: item["gap"] for name, item in calculation["categories"].items() if name != "總學分"}
    total_gap = calculation["categories"].get("總學分", {}).get("gap", 0)
    candidates = []
    for course in pool:
        code = course["code"] or course["name"]
        if not code or code in selected_codes:
            continue
        gap = gaps.get(course["category"], 0)
        mandatory = course["name"] in failed_names or bool(course.get("required", False))
        score = (100 if course["name"] in failed_names else 0) + (40 if mandatory else 0) + (20 if gap > 0 else 0)
        if total_gap <= 0 and gap <= 0 and not mandatory:
            continue
        candidates.append((score, course))
    candidates.sort(key=lambda item: (-item[0], item[1]["name"].casefold()))
    recs = []
    used = 0.0
    for score, course in candidates:
        course["recommendation_reason"] = "未過科目優先重修" if course["name"] in failed_names else (
            "補足「" + course["category"] + "」缺口" if gaps.get(course["category"], 0) > 0 else "必修課優先"
        )
        course["priority"] = score
        recs.append(course)
    return {"recommendations": recs, "selected_credits": used, "semester_limit": limit}


def simulate_selection(recommendations, selected_codes, current_earned, semester_limit=30):
    selected_codes = set(selected_codes or [])
    normalized = normalize_courses([{**course, "status": "通過"} for course in recommendations])
    available = {course["code"] or course["name"]: course for course in normalized}
    unknown = selected_codes - available.keys()
    if unknown:
        raise InputError("擬選清單含有不存在的課程。")
    selected = [available[code] for code in selected_codes]
    credits = sum(course["credits"] for course in selected)
    limit = float(semester_limit)
    if limit < 0 or limit > 30:
        raise InputError("本學期學分上限必須介於 0 到 30。")
    return {"selected_courses": selected, "selected_credits": credits, "within_limit": credits <= limit,
            "semester_limit": limit, "projected_total": float(current_earned) + credits}
