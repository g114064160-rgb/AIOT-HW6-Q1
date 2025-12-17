# 運維與操作指引

## 環境需求
- Python 3.10+（內建 sqlite3）。
- 依賴：`pip install -r requirements.txt`。
- 作業系統：Windows/Mac/Linux 皆可（本專案以 Windows 測試）。

## 匯入資料
```bash
python ingest_f_a0010_001.py --input F-A0010-001.json --db data.db
```
- 輸入支援 JSON/XML。
- 若回報「No temperature entries」：檢查文件結構與溫度欄位是否以 `T`/`TEMP` 開頭。

## 啟動前端
```bash
streamlit run app.py
```
- 在頁面輸入 SQLite 路徑（預設 `data.db`）。
- 側邊欄可篩選地區、調整顯示筆數。

## 常見檢查
- 確認表存在：
  ```bash
  sqlite3 data.db ".tables"
  ```
- 抽樣查看資料：
  ```bash
  sqlite3 data.db "SELECT l.name, t.data_time, t.temperature FROM temperatures t JOIN locations l ON t.location_id=l.id LIMIT 5;"
  ```

## 佈署建議
- 本系統預設本地執行；若需伺服器部署：
  - 以虛擬環境或容器安裝依賴。
  - 設定檔案存取權限（僅服務帳號讀寫 DB）。
  - 透過反向代理限制存取（未內建認證）。

## 備份/復原
- `data.db` 為單一檔案，可直接複製備份。
- 恢復：以備份覆蓋 `data.db` 後重啟服務。
