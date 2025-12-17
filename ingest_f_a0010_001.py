"""
Parse CWB F-A0010-001 dataset and store regional temperatures into SQLite.

Usage:
  python ingest_f_a0010_001.py --input F-A0010-001.json --db data.db

The script is defensive about format differences. It understands the typical
JSON structure returned by the CWB API (records -> location[] -> weatherElement[])
and will also attempt to read XML with the same element names. Only the built-in
sqlite3 module is used.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET


TEMP_ELEMENT_PREFIXES = ("T", "TEMP")


@dataclass
class TemperatureRow:
    location: str
    data_time: Optional[str]
    value: float
    unit: Optional[str]
    source_element: Optional[str]


def try_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def read_payload(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".json", ".txt"}:
        return json.loads(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return ET.fromstring(text)


def first_location_list(obj: Any) -> Optional[List[dict]]:
    """Breadth-first search to find the first list of locations."""
    queue: List[Any] = [obj]
    while queue:
        current = queue.pop(0)
        if isinstance(current, list):
            if current and isinstance(current[0], dict) and "locationName" in current[0]:
                return current
            queue.extend(current)
        elif isinstance(current, dict):
            for val in current.values():
                queue.append(val)
    return None


def extract_temperatures_from_json(payload: Any) -> List[TemperatureRow]:
    locations = first_location_list(payload)
    if not locations:
        return []

    rows: List[TemperatureRow] = []
    for loc in locations:
        loc_name = loc.get("locationName")
        weather_elements = (
            loc.get("weatherElement") or loc.get("weatherElements") or []
        )

        if isinstance(weather_elements, dict):
            rows.extend(
                extract_from_weather_elements_dict(loc_name, weather_elements)
            )
            continue

        for element in weather_elements:
            element_name = str(element.get("elementName", "")).upper()
            if not element_name.startswith(TEMP_ELEMENT_PREFIXES):
                continue

            times = element.get("time") or []
            if not times and isinstance(element.get("elementValue"), list):
                # Handle cases where temperature is provided without a time array.
                val, unit = extract_value_and_unit(element)
                if val is not None:
                    rows.append(
                        TemperatureRow(
                            location=loc_name,
                            data_time=None,
                            value=val,
                            unit=unit,
                            source_element=element_name,
                        )
                    )
                continue

            for time_entry in times:
                timestamp = (
                    time_entry.get("dataTime")
                    or time_entry.get("obsTime")
                    or time_entry.get("startTime")
                    or time_entry.get("endTime")
                )
                val, unit = extract_value_and_unit(time_entry)
                if val is None:
                    continue
                rows.append(
                    TemperatureRow(
                        location=loc_name,
                        data_time=timestamp,
                        value=val,
                        unit=unit,
                        source_element=element_name,
                    )
                )
    return rows


def extract_temperatures_from_xml(root: ET.Element) -> List[TemperatureRow]:
    rows: List[TemperatureRow] = []
    for location in root.findall(".//location"):
        loc_name_el = location.find("locationName")
        loc_name = loc_name_el.text.strip() if loc_name_el is not None else None
        if not loc_name:
            continue
        for element in location.findall("weatherElement"):
            element_name_el = element.find("elementName")
            element_name = (
                element_name_el.text.strip().upper() if element_name_el is not None else ""
            )
            if not element_name.startswith(TEMP_ELEMENT_PREFIXES):
                continue

            time_nodes = element.findall("time")
            if not time_nodes:
                val, unit = extract_value_and_unit(element)
                if val is not None:
                    rows.append(
                        TemperatureRow(
                            location=loc_name,
                            data_time=None,
                            value=val,
                            unit=unit,
                            source_element=element_name,
                        )
                    )
                continue

            for time_el in time_nodes:
                timestamp = (
                    text_or_none(time_el.find("dataTime"))
                    or text_or_none(time_el.find("obsTime"))
                    or text_or_none(time_el.find("startTime"))
                    or text_or_none(time_el.find("endTime"))
                )
                val, unit = extract_value_and_unit(time_el)
                if val is None:
                    continue
                rows.append(
                    TemperatureRow(
                        location=loc_name,
                        data_time=timestamp,
                        value=val,
                        unit=unit,
                        source_element=element_name,
                    )
                )
    return rows


def text_or_none(element: Optional[ET.Element]) -> Optional[str]:
    return element.text.strip() if element is not None and element.text else None


def extract_value_and_unit(node: Any) -> Tuple[Optional[float], Optional[str]]:
    val = None
    unit = None

    if isinstance(node, ET.Element):
        # XML path
        ev_nodes = node.findall("elementValue")
        if ev_nodes:
            val = text_or_none(ev_nodes[0].find("value"))
            unit = text_or_none(ev_nodes[0].find("measures"))
        else:
            parameter_node = node.find("parameter")
            if parameter_node is not None:
                val = text_or_none(parameter_node.find("parameterName"))
                unit = text_or_none(parameter_node.find("parameterUnit"))
            else:
                val = text_or_none(node.find("value"))
    else:
        # JSON path
        if "elementValue" in node:
            ev = node["elementValue"]
            if isinstance(ev, list) and ev:
                candidate = ev[0]
                val = candidate.get("value")
                unit = candidate.get("measures")
            elif isinstance(ev, dict):
                val = ev.get("value")
                unit = ev.get("measures")
        elif "parameter" in node:
            p = node["parameter"]
            if isinstance(p, list) and p:
                p = p[0]
            if isinstance(p, dict):
                val = p.get("parameterName") or p.get("parameterValue")
                unit = p.get("parameterUnit")
        else:
            for key in ("value", "temperature", "temp"):
                if key in node:
                    val = node.get(key)
                    break

    return try_float(val), unit


def extract_from_weather_elements_dict(
    location_name: str, weather_elements: dict
) -> List[TemperatureRow]:
    """
    支援 F-A0010-001 部分版本：location.weatherElements.MaxT/MinT/... -> daily[] -> temperature。
    """
    rows: List[TemperatureRow] = []
    for element_name, element_body in weather_elements.items():
        daily = element_body.get("daily") if isinstance(element_body, dict) else None
        if not daily or not isinstance(daily, list):
            continue
        for entry in daily:
            if not isinstance(entry, dict):
                continue
            timestamp = entry.get("dataDate") or entry.get("dataTime")
            val = try_float(entry.get("temperature"))
            if val is None:
                continue
            rows.append(
                TemperatureRow(
                    location=location_name,
                    data_time=timestamp,
                    value=val,
                    unit=element_body.get("units") if isinstance(element_body, dict) else None,
                    source_element=str(element_name),
                )
            )
    return rows


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS temperatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            data_time TEXT,
            temperature REAL NOT NULL,
            unit TEXT,
            source_element TEXT,
            UNIQUE(location_id, data_time, source_element),
            FOREIGN KEY(location_id) REFERENCES locations(id)
        )
        """
    )
    conn.commit()


def upsert_location(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute(
        """
        INSERT INTO locations(name) VALUES (?)
        ON CONFLICT(name) DO UPDATE SET name=excluded.name
        RETURNING id
        """,
        (name,),
    ).fetchone()
    return int(row[0])


def insert_temperatures(conn: sqlite3.Connection, rows: Sequence[TemperatureRow]) -> None:
    for row in rows:
        loc_id = upsert_location(conn, row.location)
        conn.execute(
            """
            INSERT INTO temperatures(location_id, data_time, temperature, unit, source_element)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(location_id, data_time, source_element) DO UPDATE SET
                temperature=excluded.temperature,
                unit=excluded.unit
            """,
            (loc_id, row.data_time, row.value, row.unit, row.source_element),
        )
    conn.commit()


def parse_input(path: Path) -> List[TemperatureRow]:
    payload = read_payload(path)
    if isinstance(payload, ET.Element):
        rows = extract_temperatures_from_xml(payload)
    else:
        rows = extract_temperatures_from_json(payload)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract regional temperatures from F-A0010-001 file and store into SQLite."
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to F-A0010-001 file (json or xml).")
    parser.add_argument("--db", default=Path("data.db"), type=Path, help="SQLite database path (default: data.db).")
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    rows = parse_input(args.input)
    if not rows:
        raise SystemExit("No temperature entries were found. Check that the file matches F-A0010-001 format.")

    conn = sqlite3.connect(args.db)
    try:
        ensure_schema(conn)
        insert_temperatures(conn, rows)
    finally:
        conn.close()

    print(f"Inserted/updated {len(rows)} temperature rows into {args.db}")


if __name__ == "__main__":
    main()
