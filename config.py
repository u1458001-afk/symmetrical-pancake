"""應用程式預設門檻、示範情境與安全設定。"""
import os


DEFAULT_REQUIREMENTS = {
    "總學分": 128,
    "共同必修與外語": 20,
    "通識課程": 28,
    "院系專業必修": 48,
    "系專業選修": 24,
    "跨領域／自由選修": 8,
}

# 下列為操作示範用的虛構課程，不代表聯大正式課程或學分規定。
DEMO_COURSE_POOL = [
    {"code": "DEMO-CS203", "name": "演算法", "credits": 3, "category": "院系專業必修", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-CS204", "name": "作業系統", "credits": 3, "category": "院系專業必修", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-CS301", "name": "資料庫系統", "credits": 3, "category": "院系專業必修", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-CS310", "name": "網路概論", "credits": 3, "category": "院系專業必修", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-CS320", "name": "軟體工程", "credits": 3, "category": "院系專業必修", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-CS401", "name": "人工智慧導論", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-CS402", "name": "雲端運算實務", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-CS403", "name": "人機互動設計", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-MG401", "name": "商業資料分析", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-MG402", "name": "數位行銷企劃", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-DG401", "name": "服務設計專題", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-DG402", "name": "互動介面設計", "credits": 3, "category": "系專業選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-MG499", "name": "專題實作（二）", "credits": 3, "category": "院系專業必修", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-GE101", "name": "台灣文化與社會", "credits": 2, "category": "通識課程", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-GE102", "name": "環境永續與生活", "credits": 2, "category": "通識課程", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-GE201", "name": "工程倫理", "credits": 2, "category": "通識課程", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-EN201", "name": "科技英文閱讀", "credits": 2, "category": "共同必修與外語", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-LA201", "name": "溝通與表達", "credits": 2, "category": "共同必修與外語", "required": True, "semester": "示範課程池"},
    {"code": "DEMO-XD101", "name": "設計思考與創新", "credits": 2, "category": "跨領域／自由選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-XD201", "name": "資料視覺化", "credits": 2, "category": "跨領域／自由選修", "required": False, "semester": "示範課程池"},
    {"code": "DEMO-PE101", "name": "體育與健康", "credits": 1, "category": "共同必修與外語", "required": False, "semester": "示範課程池"},
]

DEMO_SCENARIOS = {
    "a": {
        "title": "電機／資工系三年級",
        "label": "範例 A",
        "description": "含不及格必修、未過科目與已通過重修歷程。",
        "requirements": DEFAULT_REQUIREMENTS,
        "courses": [
            {"code": "DEMO-LANG1", "name": "大學國文", "credits": 4, "category": "共同必修與外語", "status": "通過", "score": 78, "semester": "112-1"},
            {"code": "DEMO-ENG1", "name": "英文（一）", "credits": 4, "category": "共同必修與外語", "status": "通過", "score": 74, "semester": "112-1"},
            {"code": "DEMO-PE", "name": "體育與健康", "credits": 2, "category": "共同必修與外語", "status": "通過", "score": 85, "semester": "112-1"},
            {"code": "DEMO-GE01", "name": "台灣文化與社會", "credits": 4, "category": "通識課程", "status": "通過", "score": 81, "semester": "112-2"},
            {"code": "DEMO-GE02", "name": "環境永續與生活", "credits": 3, "category": "通識課程", "status": "通過", "score": 76, "semester": "113-1"},
            {"code": "DEMO-GE03", "name": "工程倫理", "credits": 3, "category": "通識課程", "status": "通過", "score": 88, "semester": "113-2"},
            {"code": "DEMO-CS101", "name": "程式設計（一）", "credits": 3, "category": "院系專業必修", "status": "通過", "score": 82, "semester": "112-1"},
            {"code": "DEMO-CS102", "name": "資料結構", "credits": 3, "category": "院系專業必修", "status": "不及格", "score": 48, "semester": "112-2"},
            {"code": "DEMO-CS102", "name": "資料結構", "credits": 3, "category": "院系專業必修", "status": "通過", "score": 76, "semester": "113-1"},
            {"code": "DEMO-CS203", "name": "演算法", "credits": 3, "category": "院系專業必修", "status": "不及格", "score": 54, "semester": "113-2", "required": True},
            {"code": "DEMO-CS204", "name": "作業系統", "credits": 3, "category": "院系專業必修", "status": "通過", "score": 72, "semester": "114-1"},
            {"code": "DEMO-CS205", "name": "數位邏輯設計", "credits": 3, "category": "院系專業必修", "status": "退選", "semester": "114-1", "required": True},
            {"code": "DEMO-CS210", "name": "計算機組織", "credits": 3, "category": "院系專業必修", "status": "通過", "score": 68, "semester": "114-1"},
            {"code": "DEMO-CS301", "name": "資料庫系統", "credits": 3, "category": "系專業選修", "status": "通過", "score": 85, "semester": "114-1"},
            {"code": "DEMO-CS302", "name": "網頁應用程式", "credits": 3, "category": "系專業選修", "status": "通過", "score": 91, "semester": "114-1"},
            {"code": "DEMO-XD01", "name": "設計思考與創新", "credits": 2, "category": "跨領域／自由選修", "status": "通過", "score": 80, "semester": "113-2"},
            {"code": "DEMO-XD02", "name": "資料視覺化", "credits": 2, "category": "跨領域／自由選修", "status": "修課中", "semester": "114-2"},
        ],
        "course_pool": DEMO_COURSE_POOL,
    },
    "b": {
        "title": "管理／設計系四年級",
        "label": "範例 B",
        "description": "接近畢業門檻，聚焦最後幾個分類缺口與學分上限。",
        "requirements": DEFAULT_REQUIREMENTS,
        "courses": [
            {"code": "B-LANG", "name": "共同必修與外語修習組合", "credits": 20, "category": "共同必修與外語", "status": "通過", "score": 82, "semester": "歷年修習"},
            {"code": "B-GE1", "name": "通識課程修習組合一", "credits": 20, "category": "通識課程", "status": "通過", "score": 80, "semester": "歷年修習"},
            {"code": "B-GE2", "name": "通識課程修習組合二", "credits": 8, "category": "通識課程", "status": "通過", "score": 80, "semester": "歷年修習"},
            {"code": "B-CORE1", "name": "院系專業必修修習組合一", "credits": 24, "category": "院系專業必修", "status": "通過", "score": 78, "semester": "歷年修習"},
            {"code": "B-CORE2", "name": "院系專業必修修習組合二", "credits": 21, "category": "院系專業必修", "status": "通過", "score": 78, "semester": "歷年修習"},
            {"code": "B-EL1", "name": "系專業選修修習組合一", "credits": 20, "category": "系專業選修", "status": "通過", "score": 84, "semester": "歷年修習"},
            {"code": "B-EL2", "name": "系專業選修修習組合二", "credits": 2, "category": "系專業選修", "status": "通過", "score": 84, "semester": "歷年修習"},
            {"code": "B-XD", "name": "跨領域選修修習組合", "credits": 6, "category": "跨領域／自由選修", "status": "通過", "score": 88, "semester": "歷年修習"},
            {"code": "B-CS499", "name": "專題實作（二）", "credits": 3, "category": "院系專業必修", "status": "未通過", "score": 55, "semester": "114-1", "required": True},
        ],
        "course_pool": DEMO_COURSE_POOL,
    },
}

REQUEST_TIMEOUT = (3, float(os.getenv("COURSE_REQUEST_TIMEOUT") or "7"))
MAX_IMPORT_BYTES = 1_000_000
MAX_COURSES = 500
MAX_SEMESTER_CREDITS = 30
EXTERNAL_COURSE_URL = os.getenv("COURSE_SOURCE_URL", "").strip()
SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or "開發環境請設定正式金鑰"
