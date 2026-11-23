"""聯大學分規劃 Flask 應用程式與 JSON API。"""
import json

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

from config import (
    DEFAULT_REQUIREMENTS,
    DEMO_COURSE_POOL,
    DEMO_SCENARIOS,
    EXTERNAL_COURSE_URL,
    MAX_SEMESTER_CREDITS,
    SECRET_KEY,
)
from services.credit_engine import InputError, calculate_credits, normalize_courses
from services.course_importer import fetch_courses, import_courses
from services.course_recommender import recommend_courses, simulate_selection

app = Flask(__name__)
app.config.update(SECRET_KEY=SECRET_KEY, MAX_CONTENT_LENGTH=1_100_000)


def build_page(scenario_id="a", requirements=None, courses=None, course_pool=None, result=None, error=None, semester_limit=30, raw_inputs=None):
    scenario = DEMO_SCENARIOS.get(scenario_id, DEMO_SCENARIOS["a"])
    requirements = requirements if requirements is not None else scenario["requirements"]
    courses = courses if courses is not None else scenario["courses"]
    course_pool = course_pool if course_pool is not None else scenario["course_pool"]
    if result is None:
        calculation = calculate_credits(requirements, courses)
        result = {
            **calculation,
            **recommend_courses(course_pool, calculation, semester_limit=semester_limit),
        }
    return render_template(
        "index.html",
        error=error,
        scenario_id=scenario_id,
        scenario=scenario,
        scenarios=DEMO_SCENARIOS,
        requirements=requirements,
        courses=courses,
        course_pool=course_pool,
        requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
        courses_json=json.dumps(courses, ensure_ascii=False, indent=2),
        pool_json=json.dumps(course_pool, ensure_ascii=False, indent=2),
        raw_inputs=raw_inputs or {},
        external_course_url=EXTERNAL_COURSE_URL,
        semester_limit=semester_limit,
        result=result,
    )


def error_response(message, status=400):
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({"error": message}), status
    payload = request.form.to_dict()
    return build_page(
        "custom",
        error=message,
        raw_inputs={
            "requirements": payload.get("requirements", ""),
            "courses": payload.get("courses", ""),
            "course_pool": payload.get("course_pool", ""),
            "semester_limit": payload.get("semester_limit", "30"),
        },
    ), status


def parse_payload(payload):
    requirements = payload.get("requirements", DEFAULT_REQUIREMENTS)
    courses = payload.get("courses", [])
    pool = payload.get("course_pool", DEMO_COURSE_POOL)
    if isinstance(requirements, str):
        requirements = json.loads(requirements)
    if isinstance(courses, str):
        courses = import_courses(courses, payload.get("courses_format", "auto")) if courses.strip() else []
    if isinstance(pool, str):
        pool = import_courses(pool, payload.get("pool_format", "auto")) if pool.strip() else []
    limit = float(payload.get("semester_limit", MAX_SEMESTER_CREDITS))
    return requirements, normalize_courses(courses), normalize_courses(pool), limit


@app.get("/")
def index():
    return build_page("a")


@app.post("/calculate")
def calculate():
    try:
        payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
        payload = payload or {}
        requirements, courses, pool, limit = parse_payload(payload)
        calculation = calculate_credits(requirements, courses)
        result = {**calculation, **recommend_courses(pool, calculation, semester_limit=limit)}
        if request.is_json:
            return jsonify(result)
        return build_page(
            payload.get("scenario_id", "custom"), requirements, courses, pool,
            result=result, semester_limit=limit,
        )
    except (InputError, ValueError, TypeError, json.JSONDecodeError) as error:
        return error_response(str(error) or "輸入資料格式錯誤。")


@app.post("/api/simulate")
def simulate():
    try:
        payload = request.get_json(force=True)
        calculation = calculate_credits(payload.get("requirements", {}), payload.get("courses", []))
        result = simulate_selection(
            payload.get("recommendations", []),
            payload.get("selected_codes", []),
            calculation,
            payload.get("semester_limit", MAX_SEMESTER_CREDITS),
        )
        return jsonify(result)
    except (InputError, ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/import")
def import_endpoint():
    try:
        payload = request.get_json(force=True)
        if payload.get("url"):
            courses = fetch_courses(str(payload["url"]).strip())
        else:
            courses = import_courses(payload.get("content", ""), payload.get("format", "auto"))
        return jsonify({
            "courses": courses,
            "count": len(courses),
            "note": "匯入資料與推薦僅依來源內容推算，請自行核對官方資訊。",
        })
    except (InputError, ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(_error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=False)
