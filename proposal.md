# Streamlit App Proposal — F-A0010-001 Temperature Viewer

## 目標
建立一個本地 Streamlit 應用，讀取 SQLite 資料庫（`data.db`），顯示從 F-A0010-001 溫度匯入後的資料表格，方便檢視各地區溫度。

## 資料來源
- `data.db`：由 `ingest_f_a0010_001.py` 將 F-A0010-001 解析檔（JSON/XML）匯入後生成。
- 表格：
  - `locations(id, name)`
  - `temperatures(id, location_id, data_time, temperature, unit, source_element)`

## App 功能
1) 讀取 SQLite：使用 `sqlite3` 建立連線。
2) 顯示資料表格：
   - `temperatures` 連同 `locations.name` 做 JOIN。
   - 允許簡單篩選（地區名稱、時間排序）。
3) 基礎統計（可擴充）：顯示溫度筆數與區域數。

## 預期互動流程
1) 先執行 `ingest_f_a0010_001.py` 將資料載入 `data.db`。
2) 執行 `streamlit run app.py`。
3) 在頁面查看資料表格，必要時用側邊欄選擇地區，並按時間排序。
