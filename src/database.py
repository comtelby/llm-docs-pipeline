import sqlite3
import json
from typing import Optional

from src.config import DB_PATH
from src.eol import EOL_DATABASE


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inventories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            vendor TEXT DEFAULT '',
            category TEXT DEFAULT 'network',
            eol TEXT,
            eol_status TEXT DEFAULT 'Требуется проверка',
            specs TEXT DEFAULT '',
            source_url TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_file TEXT NOT NULL,
            prompt TEXT,
            devices_count INTEGER DEFAULT 0,
            eol_critical INTEGER DEFAULT 0,
            eol_warning INTEGER DEFAULT 0,
            issues_found INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'operator',
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def seed_eol_to_inventories():
    conn = get_connection()
    existing = conn.execute("SELECT COUNT(*) FROM inventories").fetchone()[0]
    if existing > 0:
        conn.close()
        return
    for model_key, info in EOL_DATABASE.items():
        conn.execute(
            "INSERT INTO inventories (model, vendor, eol, eol_status, specs) VALUES (?, ?, ?, ?, ?)",
            (model_key, model_key.split()[0].capitalize() if model_key.split() else "",
             info.get("eol"), info.get("status", "Требуется проверка"),
             json.dumps(info, ensure_ascii=False))
        )
    conn.commit()
    conn.close()


# ---- CRUD для inventories ----

def list_inventories(category: str = "", search: str = "") -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM inventories"
    params = []
    conditions = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    if search:
        conditions.append("(model LIKE ? OR vendor LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY vendor, model"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_inventory(model: str, vendor: str = "", category: str = "network",
                  eol: str = "", eol_status: str = "Требуется проверка",
                  specs: str = "", source_url: str = "") -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO inventories (model, vendor, category, eol, eol_status, specs, source_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (model, vendor, category, eol, eol_status, specs, source_url)
    )
    conn.commit()
    pk = cur.lastrowid
    conn.close()
    return pk


def delete_inventory(item_id: int) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM inventories WHERE id = ?", (item_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def find_inventory_by_model(model: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM inventories WHERE model LIKE ? LIMIT 1",
        (f"%{model}%",)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---- CRUD для audit_history ----

def save_audit_history(report_file: str, prompt: str = "",
                       devices_count: int = 0, eol_critical: int = 0,
                       eol_warning: int = 0, issues_found: int = 0):
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_history (report_file, prompt, devices_count, eol_critical, eol_warning, issues_found) VALUES (?, ?, ?, ?, ?, ?)",
        (report_file, prompt[:500] if prompt else "", devices_count, eol_critical, eol_warning, issues_found)
    )
    conn.commit()
    conn.close()


def list_audit_history(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM audit_history ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
