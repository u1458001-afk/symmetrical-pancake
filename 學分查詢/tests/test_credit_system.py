"""學分計算、推薦排序與匯入格式的單元測試。"""
import pytest

from services.credit_engine import InputError, calculate_credits
from services.course_importer import import_courses
from services.course_recommender import recommend_courses


def test_failed_courses_do_not_count_toward_credits():
    result = calculate_credits({"總學分": 6, "必修": 3}, [
        {"name": "程式設計", "credits": 3, "category": "必修", "status": "不及格"},
        {"name": "通識課", "credits": 3, "category": "通識", "status": "通過"},
    ])
    assert result["earned_total"] == 3
    assert result["categories"]["必修"]["gap"] == 3
    assert len(result["failed_courses"]) == 1


def test_retake_duplicate_same_term_is_counted_once():
    result = calculate_credits({"總學分": 10}, [
        {"code": "CS101", "name": "程式設計", "credits": 3, "category": "必修", "status": "通過", "semester": "114-1"},
        {"code": "CS101", "name": "程式設計", "credits": 3, "category": "必修", "status": "通過", "semester": "114-1"},
        {"code": "CS101", "name": "程式設計", "credits": 3, "category": "必修", "status": "不及格", "semester": "113-2"},
    ])
    assert result["earned_total"] == 3
    assert result["counted_course_count"] == 1
    assert len(result["failed_courses"]) == 1


def test_failed_required_course_is_recommended_first():
    result = calculate_credits({"總學分": 20, "必修": 6}, [
        {"code": "CS1", "name": "核心必修", "credits": 3, "category": "必修", "status": "未過"},
    ])
    recommendations = recommend_courses([
        {"code": "EL1", "name": "通識甲", "credits": 2, "category": "通識"},
        {"code": "CS1", "name": "核心必修", "credits": 3, "category": "必修", "required": True},
    ], result)["recommendations"]
    assert recommendations[0]["name"] == "核心必修"


def test_import_invalid_json_reports_input_error():
    with pytest.raises(InputError, match="資料格式無法解析"):
        import_courses("[{oops]", "json")


def test_import_csv_with_chinese_headers():
    courses = import_courses("課號,課程名稱,學分,類別,狀態\nA101,測試課程,2,通識,通過", "csv")
    assert courses[0]["name"] == "測試課程"
    assert courses[0]["credits"] == 2
