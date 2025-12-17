# F-A0010-001 溫度匯入至 SQLite

這個專案提供 Python 腳本，將中央氣象署 F-A0010-001 解析檔中的各地區溫度，匯入 SQLite 資料庫 `data.db`。

## 準備資料
- 下載或放置 F-A0010-001 檔案（支援 JSON 或 XML）於專案目錄。例如：`F-A0010-001.json`。
- 確認檔案內容符合官方格式：`records -> location[] -> weatherElement[]`（JSON），或對應的 XML 標籤。

## 使用方式
```bash
python ingest_f_a0010_001.py --input F-A0010-001.json --db data.db
```

參數說明：
- `--input`：F-A0010-001 解析檔路徑（必填，JSON 或 XML）。
- `--db`：輸出 SQLite 檔名，預設 `data.db`。

## 資料表設計
- `locations(id, name)`：地區名稱唯一。
- `temperatures(id, location_id, data_time, temperature, unit, source_element)`：
  - `UNIQUE(location_id, data_time, source_element)`，避免重複。
  - `data_time` 可為 `dataTime/obsTime/startTime/endTime`，腳本會自動擷取。

## 執行結果
- 成功後會在 `data.db` 寫入/更新溫度資料，終端機會顯示插入/更新的筆數。

## 查詢範例
```bash
sqlite3 data.db "SELECT l.name, t.data_time, t.temperature, t.unit FROM temperatures t JOIN locations l ON t.location_id = l.id ORDER BY t.data_time DESC LIMIT 10;"
```

## 若遇到「No temperature entries」錯誤
- 檢查輸入檔案是否為正確的 F-A0010-001 JSON/XML。
- 確認溫度欄位名稱為 `T`、`TEMP` 開頭（例：`T`、`TEMP`、`T0` 等）。
- 如使用 XML，確保有 `<weatherElement>`、`<time>` 或 `<elementValue>` 標籤。
