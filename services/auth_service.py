"""
PocketSmart AI - Authentication & Session Service
Handles secure password hashing, salt generation, session tokens,
and authentication validation.
"""

import os
import hashlib
import secrets
import json
import base64
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from database.database import get_db_connection

SECRET_KEY = os.getenv("SECRET_KEY", "pocketsmart_secure_session_key_2026_xyz")
SESSION_COOKIE_NAME = "pocketsmart_session"
SESSION_LIFETIME_DAYS = 7
PENDING_AUTH_COOKIE_NAME = "pocketsmart_pending_auth"
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_SENDS_PER_HOUR = 5

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


def generate_otp() -> str:
    """Generate a cryptographically secure six-digit one-time code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    """Hash OTPs with a server-keyed digest; plaintext codes never reach storage."""
    return hmac.new(SECRET_KEY.encode("utf-8"), otp.encode("utf-8"), hashlib.sha256).hexdigest()


def create_pending_auth_token(user_id: int, purpose: str) -> str:
    """Create a short-lived, signed browser token for an OTP challenge."""
    payload = f"{user_id}:{purpose}:{int(time.time())}".encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def read_pending_auth_token(token: Optional[str], expected_purpose: str) -> Optional[int]:
    if not token or "." not in token:
        return None
    encoded, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(SECRET_KEY.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(signature, expected_signature):
        return None
    try:
        padding = "=" * (-len(encoded) % 4)
        user_id_text, purpose, created_at_text = base64.urlsafe_b64decode(encoded + padding).decode("utf-8").split(":")
        if purpose != expected_purpose or time.time() - int(created_at_text) > OTP_EXPIRY_MINUTES * 60:
            return None
        return int(user_id_text)
    except (ValueError, TypeError, UnicodeDecodeError):
        return None


def create_otp_token(user_id: int, purpose: str) -> Tuple[str, int]:
    """Invalidate prior codes and store a new hashed code with a ten-minute expiry."""
    otp = generate_otp()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE otp_tokens SET used_at = ? WHERE user_id = ? AND purpose = ? AND used_at IS NULL",
        (now.isoformat(), user_id, purpose),
    )
    cursor.execute(
        """
        INSERT INTO otp_tokens (user_id, otp_hash, purpose, expires_at, created_at, attempt_count)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (user_id, hash_otp(otp), purpose, expires_at.isoformat(), now.isoformat()),
    )
    token_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return otp, token_id


def otp_send_allowed(user_id: int, purpose: Optional[str] = None) -> Tuple[bool, Optional[int]]:
    """Return whether a resend is allowed and remaining cooldown seconds, if any."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT created_at FROM otp_tokens WHERE user_id = ? AND created_at >= datetime('now', '-1 hour')"
    params = [user_id]
    if purpose:
        query += " AND purpose = ?"
        params.append(purpose)
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    if len(rows) >= OTP_MAX_SENDS_PER_HOUR:
        return False, None
    if rows:
        created_text = rows[0]["created_at"]
        try:
            created_at = datetime.fromisoformat(created_text.replace("Z", "+00:00"))
            remaining = OTP_RESEND_COOLDOWN_SECONDS - int((datetime.now(timezone.utc) - created_at).total_seconds())
            if remaining > 0:
                return False, remaining
        except ValueError:
            pass
    return True, None


def verify_otp_token(user_id: int, purpose: str, otp: str) -> str:
    """Verify a code and return success, invalid, expired, or locked."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, otp_hash, expires_at, used_at, attempt_count FROM otp_tokens WHERE user_id = ? AND purpose = ? ORDER BY id DESC LIMIT 1",
        (user_id, purpose),
    )
    row = cursor.fetchone()
    if not row or row["used_at"]:
        conn.close()
        return "invalid"
    try:
        if datetime.now(timezone.utc) >= datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")):
            cursor.execute("UPDATE otp_tokens SET used_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), row["id"]))
            conn.commit()
            conn.close()
            return "expired"
    except ValueError:
        conn.close()
        return "expired"
    if row["attempt_count"] >= OTP_MAX_ATTEMPTS:
        conn.close()
        return "locked"

    if not secrets.compare_digest(row["otp_hash"], hash_otp(otp.strip())):
        next_attempt = row["attempt_count"] + 1
        used_at = datetime.now(timezone.utc).isoformat() if next_attempt >= OTP_MAX_ATTEMPTS else None
        cursor.execute("UPDATE otp_tokens SET attempt_count = ?, used_at = ? WHERE id = ?", (next_attempt, used_at, row["id"]))
        conn.commit()
        conn.close()
        return "locked" if used_at else "invalid"

    cursor.execute("UPDATE otp_tokens SET used_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), row["id"]))
    conn.commit()
    conn.close()
    return "success"

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
             u.id, u.username, u.email, u.full_name, u.created_at, u.email_verified, u.email_verified_at
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ?
    """, (session_token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    if not bool(row["email_verified"]):
        delete_session(session_token)
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
        "email_verified": bool(row["email_verified"]),
        "email_verified_at": row["email_verified_at"],
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
