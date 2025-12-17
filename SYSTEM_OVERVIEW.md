# 系統總覽

本系統目的：將中央氣象署 F-A0010-001 解析檔（JSON/XML）中的各地區溫度匯入 SQLite，並以 Streamlit 提供本地瀏覽界面。

## 模組
- 資料匯入：`ingest_f_a0010_001.py` 解析 F-A0010-001 並寫入 `data.db`。
- 資料庫：`data.db`（SQLite），表 `locations`、`temperatures`。
- 前端：`app.py`（Streamlit），讀取資料庫並顯示表格與統計。
- 文件：`README.md`（操作）、`proposal.md`（App 規劃）、本文件（總覽）、`ARCHITECTURE.md`（技術細節）、`OPERATIONS.md`（運維指引）。

## 主要流程
1. 取得 F-A0010-001 檔案（JSON/XML）。
2. 執行匯入腳本：`python ingest_f_a0010_001.py --input <file> --db data.db`。
3. 啟動 Streamlit：`streamlit run app.py`，輸入資料庫路徑檢視資料。

## 關鍵假設
- F-A0010-001 結構包含 `location` + `weatherElement`，溫度欄位以 `T`/`TEMP` 開頭。
- SQLite 檔案放在本機；無額外網路需求（除非下載來源檔）。

## 資安/存取
- 全部在本機檔案系統運行；無遠端資料庫與網路 API。
- 如需遠端部署，需新增認證與網路安全設定（未實作）。
