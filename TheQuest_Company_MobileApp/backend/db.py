"""
Database connection and resolution module for The Quest Mobile App.
Finds the shared hotel_service.db and ensures tables are ready.
"""

import os
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager

BACKEND_DIR = Path(__file__).resolve().parent
APP_DIR = BACKEND_DIR.parent
PROJECT_ROOT = APP_DIR.parent

# Database path in shared database directory
DATABASE_PATH = PROJECT_ROOT / "database" / "hotel_service.db"


def get_db_path() -> Path:
    """Return the absolute path to hotel_service.db, ensuring directories exist."""
    if DATABASE_PATH.exists():
        return DATABASE_PATH
    # Fallback to local copy if running standalone
    local_db = APP_DIR / "hotel_service.db"
    if local_db.exists():
        return local_db
    return DATABASE_PATH


@contextmanager
def get_connection():
    """Context manager for SQLite database connection with row factory."""
    db_path = get_db_path()
    # If db file doesn't exist yet, attempt initialization
    if not db_path.exists():
        init_database_if_needed()

    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_db(query: str, args=(), one: bool = False):
    """Convenience helper to run a SELECT query and return dict or list of dicts."""
    with get_connection() as conn:
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        if one:
            return dict(rv[0]) if rv else None
        return [dict(row) for row in rv]


def execute_db(query: str, args=()) -> int:
    """Convenience helper to run an INSERT/UPDATE/DELETE query and return lastrowid."""
    with get_connection() as conn:
        cur = conn.execute(query, args)
        last_id = cur.lastrowid
        cur.close()
        return last_id


def init_database_if_needed():
    """Initialize schema and seed data if database file does not exist or users table is empty."""
    db_path = get_db_path()
    db_dir = db_path.parent
    db_dir.mkdir(parents=True, exist_ok=True)

    db_scripts_dir = PROJECT_ROOT / "database"
    if str(db_scripts_dir) not in sys.path:
        sys.path.insert(0, str(db_scripts_dir))

    try:
        from setup_db import create_database
        create_database()
    except Exception as e:
        print(f"[Mobile App] Warning during create_database: {e}")

    try:
        conn = sqlite3.connect(str(db_path))
        u_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
        conn.close()
        if u_count == 0:
            from seed_data import seed_database
            seed_database()
            print("[Mobile App] Database automatically seeded.")
    except Exception as e:
        print(f"[Mobile App] Seeding check note: {e}")
