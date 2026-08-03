"""SQLite access layer for the info table and the meetings table."""

import json
import os
import sqlite3

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "info.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None: #This function does not return a value.
    os.makedirs(DB_DIR, exist_ok=True)
    conn = _get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                participants TEXT NOT NULL,
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'scheduled',
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_info(category: str, content: str) -> dict:#This function is a helper used to insert test or reference data into the info table.
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO info (category, content) VALUES (?, ?)",
            (category, content),
        )
        conn.commit()#saves the inserted row
        return get_info_entry(cursor.lastrowid)#instead of returning just the ID, this function returns the complete newly created record
    finally:
        conn.close()


def get_info_entry(info_id: int) -> dict:#retrieves one piece of information from the database using its id
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM info WHERE id = ?", (info_id,)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_info_entries(query: str) -> list[str]:#This function is the database search part
    """Keyword search over info.content: matches rows containing any word from the
    query (not just the whole phrase). Returns matching content strings, empty if
    none/no data."""
    words = [w for w in query.split() if w]
    if not words:
        return []

    conn = _get_conn()
    try:
        clause = " OR ".join(["content LIKE ?"] * len(words))
        params = [f"%{w}%" for w in words]
        rows = conn.execute(
            f"SELECT content FROM info WHERE {clause} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [row["content"] for row in rows]
    finally:
        conn.close()


def _meeting_row_to_dict(row: sqlite3.Row) -> dict:
    record = dict(row)
    record["participants"] = json.loads(record["participants"])
    return record


def insert_meeting(
    title: str,
    start_time: str,
    end_time: str,
    participants: list[str],
    notes: str = "",
) -> dict:
    conn = _get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO meetings (title, start_time, end_time, participants, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, start_time, end_time, json.dumps(participants), notes),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _meeting_row_to_dict(row)
    finally:
        conn.close()


def list_meetings(from_date: str = None, to_date: str = None) -> list[dict]:
    """Returns non-cancelled meetings, optionally filtered by an ISO date/datetime range."""
    conn = _get_conn()
    try:
        query = "SELECT * FROM meetings WHERE status != 'cancelled'"
        params = []
        if from_date:
            query += " AND start_time >= ?"
            params.append(from_date)
        if to_date:
            query += " AND start_time <= ?"
            params.append(to_date)
        query += " ORDER BY start_time ASC"
        rows = conn.execute(query, params).fetchall()
        return [_meeting_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_meeting(meeting_id: int) -> dict:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        return _meeting_row_to_dict(row) if row else {}
    finally:
        conn.close()


def set_meeting_status(meeting_id: int, status: str) -> dict:
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE meetings SET status = ? WHERE id = ?", (status, meeting_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        return _meeting_row_to_dict(row) if row else {}
    finally:
        conn.close()
