"""學分門檻、成績、重修、推薦與課程匯入的單元測試。"""
from unittest.mock import Mock

import pytest
import requests

from services.credit_engine import InputError, calculate_credits
from services.course_importer import fetch_courses, import_courses
from services.course_recommender import recommend_courses, simulate_selection


def test_score_under_sixty_counts_as_zero_and_needs_retake():
    result = calculate_credits({"總學分": 3, "院系專業必修": 3}, [
        {"code": "CS101", "name": "程式設計", "credits": 3, "category": "院系專業必修", "status": "通過", "score": 59},
    ])
    assert result["earned_total"] == 0
    assert result["categories"]["院系專業必修"]["gap"] == 3
    assert result["failed_courses"][0]["outcome"] == "未通過"


def test_failed_status_counts_zero_even_when_score_is_missing():
    result = calculate_credits({"總學分": 4}, [
        {"name": "停修課程", "credits": 4, "category": "通識課程", "status": "停修"},
        {"name": "退選課程", "credits": 2, "category": "通識課程", "status": "退選"},
    ])
    assert result["earned_total"] == 0
    assert len(result["failed_courses"]) == 2


def test_retake_is_counted_once_and_resolved_course_leaves_failed_list():
    result = calculate_credits({"總學分": 10}, [
        {"code": "CS101", "name": "程式設計", "credits": 3, "category": "院系專業必修", "status": "不及格", "score": 48, "semester": "112-2"},
        {"code": "CS101", "name": "程式設計", "credits": 3, "category": "院系專業必修", "status": "通過", "score": 72, "semester": "113-1"},
    ])
    assert result["earned_total"] == 3
    assert result["counted_course_count"] == 1
    assert result["failed_courses"] == []
    assert result["retake_history"][0]["attempt_count"] == 2
    assert result["retake_history"][0]["resolved"] is True


def test_course_name_normalization_deduplicates_without_matching_code():
    result = calculate_credits({"總學分": 10}, [
        {"name": "資料結構", "credits": 3, "category": "院系專業必修", "status": "通過", "semester": "113-1"},
        {"name": " 資料　結構 ", "credits": 3, "category": "院系專業必修", "status": "通過", "semester": "114-1"},
    ])
    assert result["earned_total"] == 3
    assert len(result["retake_history"]) == 1


def test_failed_required_course_is_recommended_first():
    calculation = calculate_credits({"總學分": 20, "院系專業必修": 6}, [
        {"code": "CS1", "name": "核心必修", "credits": 3, "category": "院系專業必修", "status": "未過", "required": True},
    ])
    result = recommend_courses([
        {"code": "EL1", "name": "通識甲", "credits": 2, "category": "通識課程"},
        {"code": "CS1", "name": "核心必修", "credits": 3, "category": "院系專業必修", "required": True},
    ], calculation)
    assert result["recommendations"][0]["name"] == "核心必修"
    assert result["recommendations"][0]["priority"] == 0


def test_largest_category_gap_sorts_ahead_of_other_gaps():
    calculation = calculate_credits({"總學分": 20, "通識課程": 8, "系專業選修": 5}, [
        {"name": "通識甲", "credits": 2, "category": "通識課程", "status": "通過"},
    ])
    result = recommend_courses([
        {"code": "EL1", "name": "系選修", "credits": 3, "category": "系專業選修"},
        {"code": "GE1", "name": "通識乙", "credits": 2, "category": "通識課程"},
    ], calculation)
    assert result["largest_gap_categories"] == ["通識課程"]
    assert result["recommendations"][0]["name"] == "通識乙"


def test_simulation_reports_category_and_total_gaps():
    calculation = calculate_credits({"總學分": 10, "通識課程": 5}, [
        {"name": "通識已修", "credits": 2, "category": "通識課程", "status": "通過"},
    ])
    result = simulate_selection([
        {"code": "GE1", "name": "通識推薦", "credits": 2, "category": "通識課程"},
    ], ["GE1"], calculation, semester_limit=3)
    assert result["remaining_gaps"]["總學分"] == 6
    assert result["remaining_gaps"]["通識課程"] == 1
    assert result["within_limit"] is True


def test_import_invalid_json_reports_input_error():
    with pytest.raises(InputError, match="資料格式無法解析"):
        import_courses("[{oops]", "json")


def test_import_csv_and_simple_text():
    csv_courses = import_courses("課號,課程名稱,學分,類別,狀態\nA101,測試課程,2,通識課程,通過", "csv")
    text_courses = import_courses("A102 | 另一門課 | 3 | 院系專業必修", "text")
    assert csv_courses[0]["name"] == "測試課程"
    assert csv_courses[0]["credits"] == 2
    assert text_courses[0]["code"] == "A102"
    assert text_courses[0]["name"] == "另一門課"


def test_fetch_courses_uses_timeout_and_user_agent(monkeypatch):
    monkeypatch.setattr("services.course_importer.socket.getaddrinfo", lambda *_args, **_kwargs: [(None, None, None, None, ("93.184.216.34", 443))])
    response = Mock(status_code=200, content=b"code,name,credits,category\nCS1,測試課程,3,院系專業必修", headers={"Content-Type": "text/csv"})
    response.raise_for_status.return_value = None
    get = Mock(return_value=response)
    monkeypatch.setattr("services.course_importer.requests.get", get)
    result = fetch_courses("https://courses.example/term.csv")
    assert result[0]["name"] == "測試課程"
    assert get.call_args.kwargs["timeout"] == (3, 7.0)
    assert get.call_args.kwargs["headers"]["User-Agent"] == "NUU-Credit-Planner/1.0"


def test_import_api_returns_mocked_external_courses(monkeypatch):
    from app import app

    monkeypatch.setattr("services.course_importer.socket.getaddrinfo", lambda *_args, **_kwargs: [(None, None, None, None, ("93.184.216.34", 443))])
    response = Mock(status_code=200, content=b"code,name,credits,category\nCS1,測試課程,3,院系專業必修", headers={"Content-Type": "text/csv"})
    response.raise_for_status.return_value = None
    monkeypatch.setattr("services.course_importer.requests.get", Mock(return_value=response))
    client = app.test_client()
    result = client.post("/api/import", json={"url": "https://courses.example/term.csv"})
    assert result.status_code == 200
    assert result.get_json()["courses"][0]["name"] == "測試課程"


def test_fetch_timeout_has_clear_error(monkeypatch):
    monkeypatch.setattr("services.course_importer.socket.getaddrinfo", lambda *_args, **_kwargs: [(None, None, None, None, ("93.184.216.34", 443))])
    monkeypatch.setattr("services.course_importer.requests.get", Mock(side_effect=requests.Timeout))
    with pytest.raises(InputError, match="逾時"):
        fetch_courses("https://courses.example/term.json")
