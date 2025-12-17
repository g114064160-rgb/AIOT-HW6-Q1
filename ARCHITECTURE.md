# 系統架構與資料設計

## 組件
- **ingest_f_a0010_001.py**
  - 讀取 JSON/XML。
  - 抽取溫度：搜尋 `records -> location[] -> weatherElement[]`，僅保留 `elementName` 以 `T`/`TEMP` 開頭。
  - 寫入 SQLite：`locations`、`temperatures`，含唯一鍵 `(location_id, data_time, source_element)`。
- **SQLite (`data.db`)**
  - 表：
    - `locations(id, name UNIQUE)`
    - `temperatures(id, location_id FK, data_time, temperature REAL, unit, source_element, UNIQUE(location_id, data_time, source_element))`
- **app.py (Streamlit)**
  - `sqlite3` 連線（`st.cache_resource`）。
  - JOIN `temperatures` + `locations` 顯示表格，側邊欄篩選地區、控制筆數；顯示區域數與筆數。

## 資料流程
1. 來源檔 → 解析（JSON/XML）→ 溫度資料列。
2. SQLite 寫入：確保地區唯一、溫度紀錄唯一。
3. Streamlit 查詢：JOIN 後排序（`data_time DESC NULLS LAST`）並顯示。

## 錯誤處理
- 解析不到溫度時終止並提示。
- SQLite 寫入使用 `ON CONFLICT` 更新，避免重複。
- Streamlit 若找不到 DB，顯示警告並停止。

## 可擴充點
- 新增其他氣象要素：擴增 `weatherElement` 篩選。
- 遠端部署：包裝為容器，增加認證與環境變數設定。
- 視覺化：於 Streamlit 增加圖表（折線、分佈）。
