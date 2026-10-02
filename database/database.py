"""
PocketSmart AI - Database Module
SQLite-based clean database access layer with connection management,
schema initialization, and helper operations.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./pocketsmart.db").replace("sqlite:///", "")

def get_db_connection() -> sqlite3.Connection:
    """Create and return a thread-safe sqlite3 connection with Row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        email_verified INTEGER NOT NULL DEFAULT 0,
        email_verified_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe migration for databases created before email verification existed.
    cursor.execute("PRAGMA table_info(users)")
    user_columns = {row[1] for row in cursor.fetchall()}
    if "email_verified" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
    if "email_verified_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email_verified_at TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        otp_hash TEXT NOT NULL,
        purpose TEXT NOT NULL CHECK (purpose IN ('EMAIL_VERIFICATION', 'LOGIN')),
        expires_at TEXT NOT NULL,
        used_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp_tokens_user_purpose ON otp_tokens(user_id, purpose)")

    # Planner Requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planner_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        planner_type TEXT NOT NULL,
        total_budget REAL NOT NULL,
        input_data TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # Recommendation History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendation_histories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        planner_request_id INTEGER,
        planner_type TEXT NOT NULL,
        total_budget REAL NOT NULL,
        allocated_spend REAL NOT NULL,
        estimated_travel REAL DEFAULT 0.0,
        remaining_budget REAL NOT NULL,
        status TEXT NOT NULL,
        summary_text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (planner_request_id) REFERENCES planner_requests (id) ON DELETE SET NULL
    );
    """)

    # Recommendation Results (Items/Places)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        history_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        quantity INTEGER DEFAULT 1,
        total_price REAL NOT NULL,
        platform TEXT NOT NULL,
        url TEXT NOT NULL,
        reason TEXT,
        distance_km REAL,
        travel_time_minutes INTEGER,
        travel_cost_estimate REAL,
        rating REAL,
        review_count INTEGER,
        location TEXT,
        is_mock INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (history_id) REFERENCES recommendation_histories (id) ON DELETE CASCADE
    );
    """)

    # Product Scans & Price Comparisons
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT NOT NULL,
        brand TEXT,
        model TEXT,
        variant TEXT,
        match_confidence TEXT NOT NULL,
        category TEXT,
        local_price REAL NOT NULL,
        lowest_online_price REAL,
        price_difference REAL,
        possible_saving REAL,
        online_prices_json TEXT NOT NULL,
        image_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # User Sessions / State cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL,
        session_data TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
