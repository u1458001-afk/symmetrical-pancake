# 聯大學分規劃

提供國立聯合大學學生自行整理畢業學分門檻、修課紀錄、未過科目與擬選課程的 Flask 網頁工具。所有結果均為「依目前輸入門檻、修課紀錄與課程池推算」，請以聯大教務處、所屬系辦公告及擋修規定為準。

## 本機啟動

需要 Python 3.12。於專案目錄執行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

開啟終端機顯示的本機網址即可使用。若環境沒有 `py` 啟動器，請以已安裝的 Python 3.12 執行相同的虛擬環境與安裝步驟。

## 輸入格式

修課紀錄 JSON 範例：

```json
[
  {"code":"CS101","name":"程式設計","credits":3,"category":"必修","status":"通過","semester":"114-1"},
  {"code":"GE201","name":"通識課","credits":2,"category":"通識","status":"不及格","semester":"114-1"}
]
```

課程狀態請使用「通過」、「不及格」或「修課中」；未過與修課中不會計入已取得學分。同一課號（沒有課號時以課名判斷）只計入一次。CSV 第一列需包含欄位名稱，可使用中文欄名「課號、課程名稱、學分、類別、狀態、學期」，或英文對應欄名。

## 選填外部課程來源

`COURSE_SOURCE_URL` 可設定為你信任的 HTTPS JSON 或 CSV 網址；空白時不啟用外部讀取。來源需提供課號、課名、學分及類別欄位，並允許伺服器端讀取。應確認資料授權與更新日期；程式不會將外部來源宣稱為聯大官方資料。請勿把金鑰或含機密的網址放入版控。

## Vercel 部署

將專案匯入 Vercel，並設定必要的 `FLASK_SECRET_KEY`（選填設定 `COURSE_SOURCE_URL`、`COURSE_REQUEST_TIMEOUT`）。`.python-version` 固定 Python 3.12；`vercel.json` 將所有路徑轉送至 `api/index.py`。部署執行環境不寫入本機資料；使用者草稿由瀏覽器 `localStorage` 暫存，也可匯入、匯出 JSON／CSV。

## 測試

安裝相依套件後，在專案根目錄執行 `pytest`。測試涵蓋不及格不計學分、重修去重、未過必修推薦排序，以及錯誤匯入與中文 CSV 欄名。
