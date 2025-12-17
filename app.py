import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH_DEFAULT = Path("data.db")


@st.cache_resource
def get_conn(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def load_data(conn: sqlite3.Connection, region: str | None, limit: int | None) -> pd.DataFrame:
    base_query = """
        SELECT
            l.name AS location,
            t.data_time,
            t.temperature,
            t.unit,
            t.source_element
        FROM temperatures t
        JOIN locations l ON t.location_id = l.id
    """
    clauses = []
    params: list[str] = []
    if region:
        clauses.append("l.name = ?")
        params.append(region)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order = "ORDER BY t.data_time DESC NULLS LAST"
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"{base_query} {where} {order} {limit_clause}"
    return pd.read_sql_query(query, conn, params=params)


def load_regions(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM locations ORDER BY name").fetchall()
    return [r[0] for r in rows]


def load_counts(conn: sqlite3.Connection) -> tuple[int, int]:
    loc_count = conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
    temp_count = conn.execute("SELECT COUNT(*) FROM temperatures").fetchone()[0]
    return loc_count, temp_count


def main() -> None:
    st.title("F-A0010-001 溫度資料瀏覽")
    db_path_str = st.text_input("SQLite 檔案路徑", value=str(DB_PATH_DEFAULT))
    db_path = Path(db_path_str)

    if not db_path.exists():
        st.warning(f"找不到資料庫：{db_path}. 請先執行 ingest_f_a0010_001.py 匯入資料。")
        return

    conn = get_conn(db_path)

    with st.sidebar:
        st.header("篩選")
        regions = load_regions(conn)
        region = st.selectbox("地區", options=["(全部)"] + regions)
        region = None if region == "(全部)" else region
        limit = st.slider("顯示筆數", min_value=10, max_value=500, value=100, step=10)

    loc_count, temp_count = load_counts(conn)
    st.write(f"目前共有 **{loc_count}** 個地區，**{temp_count}** 筆溫度紀錄。")

    df = load_data(conn, region=region, limit=limit)
    if df.empty:
        st.info("沒有資料可顯示，請確認資料庫已匯入。")
        return

    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
