"""
PocketSmart AI - Authentication & Session Service
Handles secure password hashing, salt generation, session tokens,
and authentication validation.
"""

import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from database.database import get_db_connection

SECRET_KEY = os.getenv("SECRET_KEY", "pocketsmart_secure_session_key_2026_xyz")
SESSION_COOKIE_NAME = "pocketsmart_session"
SESSION_LIFETIME_DAYS = 7

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against salt:hash format."""
    try:
        parts = hashed.split(":")
        if len(parts) != 2:
            return False
        salt, expected_hex = parts
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False

def create_session(user_id: int, initial_data: Optional[Dict[str, Any]] = None) -> str:
    """Create a new session record in user_sessions table and return session token."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_LIFETIME_DAYS)).isoformat()
    session_data = json.dumps(initial_data or {})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_sessions (session_token, user_id, expires_at, session_data)
        VALUES (?, ?, ?, ?)
    """, (token, user_id, expires_at, session_data))
    conn.commit()
    conn.close()
    return token

def delete_session(session_token: str):
    """Delete a session by token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()

def get_current_user_from_token(session_token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary given a session token, if valid and not expired."""
    if not session_token:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.session_token, s.user_id, s.expires_at, s.session_data,
               u.id, u.username, u.email, u.full_name, u.created_at
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ?
    """, (session_token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    
    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            delete_session(session_token)
            return None
    except Exception:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
        "created_at": row["created_at"],
        "session_token": row["session_token"],
        "session_data": json.loads(row["session_data"] or "{}")
    }

def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Extract user from Cookie or Authorization header without raising exception."""
    # 1. Check Cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)
    
    # 2. Check Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            
    return get_current_user_from_token(token)

def get_current_user_required(request: Request) -> Dict[str, Any]:
    """Extract current user or raise 401 / redirect depending on request accept header."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please login."
        )
    return user

def update_session_data(session_token: str, key: str, value: Any):
    """Store personalization or temporary preference in user's active session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_data FROM user_sessions WHERE session_token = ?", (session_token,))
    row = cursor.fetchone()
    if row:
        data = json.loads(row["session_data"] or "{}")
        data[key] = value
        cursor.execute("UPDATE user_sessions SET session_data = ? WHERE session_token = ?", (json.dumps(data), session_token))
        conn.commit()
    conn.close()
