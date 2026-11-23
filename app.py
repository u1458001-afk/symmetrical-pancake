"""聯大學分缺口與選課規劃 Flask 應用程式。"""
import json

from flask import Flask, jsonify, render_template, request

from config import DEFAULT_REQUIREMENTS, DEMO_COURSES, EXTERNAL_COURSE_URL, MAX_SEMESTER_CREDITS, SECRET_KEY
from services.credit_engine import InputError, calculate_credits, normalize_courses
from services.course_importer import fetch_courses, import_courses
from services.course_recommender import recommend_courses, simulate_selection

app = Flask(__name__)
app.config.update(SECRET_KEY=SECRET_KEY, MAX_CONTENT_LENGTH=1_100_000)


def error_response(message, status=400):
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({"error": message}), status
    return render_template("index.html", error=message, requirements=DEFAULT_REQUIREMENTS,
                          courses=DEMO_COURSES, course_pool=DEMO_COURSES,
                          requirements_json=json.dumps(DEFAULT_REQUIREMENTS, ensure_ascii=False),
                          courses_json="[]", pool_json=json.dumps(DEMO_COURSES, ensure_ascii=False),
                          external_course_url=EXTERNAL_COURSE_URL, result=None), status


def parse_payload(payload):
    requirements = payload.get("requirements", DEFAULT_REQUIREMENTS)
    courses = payload.get("courses", [])
    pool = payload.get("course_pool", DEMO_COURSES)
    if isinstance(requirements, str):
        requirements = json.loads(requirements)
    if isinstance(courses, str):
        courses = import_courses(courses, payload.get("courses_format", "auto")) if courses.strip() else []
    if isinstance(pool, str):
        pool = import_courses(pool, payload.get("pool_format", "auto")) if pool.strip() else []
    semester_limit = float(payload.get("semester_limit", MAX_SEMESTER_CREDITS))
    return requirements, normalize_courses(courses), normalize_courses(pool), semester_limit


@app.get("/")
def index():
    return render_template("index.html", error=None, requirements=DEFAULT_REQUIREMENTS,
                           courses=DEMO_COURSES, course_pool=DEMO_COURSES,
                           requirements_json=json.dumps(DEFAULT_REQUIREMENTS, ensure_ascii=False),
                           courses_json="[]", pool_json=json.dumps(DEMO_COURSES, ensure_ascii=False),
                           external_course_url=EXTERNAL_COURSE_URL, result=None)


@app.post("/calculate")
def calculate():
    try:
        payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
        payload = payload or {}
        requirements, courses, pool, semester_limit = parse_payload(payload)
        calculation = calculate_credits(requirements, courses)
        recommendation = recommend_courses(pool, calculation)
        result = {**calculation, **recommendation}
        if request.is_json:
            return jsonify(result)
        return render_template("index.html", error=None, requirements=requirements, courses=courses,
                               course_pool=pool, requirements_json=json.dumps(requirements, ensure_ascii=False),
                               courses_json=json.dumps(courses, ensure_ascii=False),
                               pool_json=json.dumps(pool, ensure_ascii=False), external_course_url=EXTERNAL_COURSE_URL,
                               result=result)
    except (InputError, ValueError, TypeError, json.JSONDecodeError) as error:
        return error_response(str(error) or "輸入資料格式錯誤。")


@app.post("/api/simulate")
def simulate():
    try:
        payload = request.get_json(force=True)
        courses = normalize_courses(payload.get("recommendations", []))
        result = simulate_selection(courses, payload.get("selected_codes", []),
                                    payload.get("current_earned", 0), payload.get("semester_limit", MAX_SEMESTER_CREDITS))
        return jsonify(result)
    except (InputError, ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/import")
def import_endpoint():
    try:
        payload = request.get_json(force=True)
        if payload.get("url"):
            requested_url = str(payload["url"]).strip()
            if not EXTERNAL_COURSE_URL or requested_url != EXTERNAL_COURSE_URL:
                raise InputError("外部來源網址尚未設定，或與伺服器設定不符。")
            courses = fetch_courses(requested_url)
        else:
            courses = import_courses(payload.get("content", ""), payload.get("format", "auto"))
        return jsonify({"courses": courses, "count": len(courses),
                        "note": "此為匯入來源資料，請自行確認是否為聯大最新官方開課資訊。"})
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
