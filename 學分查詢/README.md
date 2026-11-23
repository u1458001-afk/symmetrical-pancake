# 聯大學分規劃

為國立聯合大學學生整理的學分盤點與擬選工具，提供缺口拆解、未過科目追蹤、重修去重、課程推薦與學分上限試算。所有結果皆為「依目前輸入門檻、修課紀錄與課程池推算」，請以聯大教務處、所屬系辦公告及擋修規定為準。

## 開箱試用

首頁預設載入「範例 A：電機／資工系三年級」，也可切換「範例 B：管理／設計系四年級」。兩組資料、課程名稱和門檻都是操作示意，**不是聯大官方課程或畢業規定**。可用「清空重填」移除修課紀錄，再從快速新增或資料管理開始輸入。

畫面提供即時關鍵字搜尋（支援 `/` 聚焦）、修課與推薦快篩、Enter 快速新增、擬選缺口試算、學分上限提醒，以及 JSON／CSV 匯入匯出。輸入資料暫存在瀏覽器 `localStorage`，Flask 不會將個人修課資料寫入伺服器檔案。

## 修課資料格式

可貼上 JSON、含欄名的 CSV，或每行一門課的簡易文字。簡易文字可用 `|` 或 Tab 分隔：

```text
CS101 | 程式設計（一） | 3 | 院系專業必修
通識課程甲 | 2 | 通識課程
```

JSON 課程欄位可使用 `code`、`name`、`credits`、`category`、`status`、`score`、`semester`、`required`；也支援相對應的中文欄名。成績低於 60 分、未通過、不及格、退選、停修或零分都不計學分。同課號或同名課程只計入一次；通過重修後會保留歷程，並從仍需補過清單移除。

## 本機啟動

需要 Python 3.12。於專案目錄執行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

開啟 Flask 顯示的本機網址即可使用。若沒有 `py` 啟動器，請以已安裝的 Python 3.12 執行相同的虛擬環境與安裝步驟。

## 外部課程清單

在資料管理區輸入 HTTPS JSON／CSV 網址，或直接貼上 JSON、CSV、簡易文字。外部 URL 讀取透過 `requests`，連線逾時 3 秒、讀取逾時預設 7 秒，並檢查公開網路位址、限制重新導向及回應大小。來源資料仍須自行確認授權、學期與更新時間；不會假稱為校務系統或官方課表。

部署環境可選擇設定 `COURSE_SOURCE_URL` 作為預填網址，並透過 `COURSE_REQUEST_TIMEOUT` 調整讀取逾時秒數。正式環境請在平台設定 `FLASK_SECRET_KEY`。所有範例變數均留空於 `.env.example`。

## Vercel 部署

將專案匯入 Vercel，`.python-version` 固定 Python 3.12，`api/index.py` 匯入 Flask 應用程式並由 `vercel.json` 接收路徑。Serverless 不使用 SQLite 或本機檔案儲存；使用者資料以瀏覽器暫存或 JSON／CSV 處理。

## 測試

安裝相依套件後，在專案根目錄執行 `pytest`。測試涵蓋未達 60 分與不及格狀態、重修去重與歷程、推薦優先序、擬選缺口、JSON／CSV／簡易文字解析，以及使用 mock 驗證外部請求逾時與 User-Agent。
