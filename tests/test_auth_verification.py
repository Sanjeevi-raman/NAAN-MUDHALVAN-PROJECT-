import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from database.database import get_db_connection, init_db
from main import app
from services.auth_service import PENDING_AUTH_COOKIE_NAME, create_session, hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_auth_db(monkeypatch):
    sent_codes = {}

    def fake_verification(email, otp):
        sent_codes["verification"] = (email, otp)

    def fake_login(email, otp):
        sent_codes["login"] = (email, otp)

    monkeypatch.setattr("routes.auth.send_verification_otp", fake_verification)
    monkeypatch.setattr("routes.auth.send_login_otp", fake_login)
    monkeypatch.setenv("LOGIN_OTP_ENABLED", "false")
    client.cookies.clear()
    init_db()
    conn = get_db_connection()
    conn.execute("DELETE FROM user_sessions")
    conn.execute("DELETE FROM otp_tokens")
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    yield sent_codes


def register(username="verify_user", email="verify@example.com", password="password123"):
    return client.post("/register", data={
        "full_name": "Verification User",
        "username": username,
        "email": email,
        "password": password,
    }, follow_redirects=False)


def mark_verified(username):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.execute("UPDATE users SET email_verified = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return create_session(row["id"])


def test_registration_creates_unverified_hashed_otp(clean_auth_db):
    response = register()
    assert response.status_code == 303
    assert response.headers["location"] == "/verify-email"
    assert response.cookies.get(PENDING_AUTH_COOKIE_NAME)
    assert "pocketsmart_session" not in response.cookies

    conn = get_db_connection()
    user = conn.execute("SELECT email_verified FROM users WHERE email = ?", ("verify@example.com",)).fetchone()
    token = conn.execute("SELECT otp_hash FROM otp_tokens WHERE purpose = 'EMAIL_VERIFICATION'").fetchone()
    conn.close()
    assert user["email_verified"] == 0
    assert token["otp_hash"] != clean_auth_db["verification"][1]
    assert len(clean_auth_db["verification"][1]) == 6


def test_invalid_email_and_duplicate_email(clean_auth_db):
    invalid = register(email="not-an-email")
    assert invalid.status_code == 400
    assert "valid email" in invalid.text
    assert register().status_code == 303
    duplicate = register(username="other_user")
    assert duplicate.status_code == 400
    assert "already registered" in duplicate.text


def test_correct_otp_verifies_and_used_otp_is_rejected(clean_auth_db):
    register()
    code = clean_auth_db["verification"][1]
    verified = client.post("/verify-email", data={"otp": code}, follow_redirects=False)
    assert verified.status_code == 303
    assert verified.headers["location"] == "/dashboard"
    assert verified.cookies.get("pocketsmart_session")

    reused = client.post("/verify-email", data={"otp": code})
    assert reused.status_code == 400
    assert "Invalid verification code" in reused.text

    conn = get_db_connection()
    row = conn.execute("SELECT email_verified, email_verified_at FROM users WHERE email = ?", ("verify@example.com",)).fetchone()
    conn.close()
    assert row["email_verified"] == 1
    assert row["email_verified_at"] is not None


def test_expired_otp_has_specific_message(clean_auth_db):
    register()
    conn = get_db_connection()
    conn.execute("UPDATE otp_tokens SET expires_at = ?", ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),))
    conn.commit()
    conn.close()
    response = client.post("/verify-email", data={"otp": clean_auth_db["verification"][1]})
    assert response.status_code == 400
    assert "This code has expired. Request a new code." in response.text


def test_resend_invalidates_previous_otp(clean_auth_db):
    register()
    old_code = clean_auth_db["verification"][1]
    conn = get_db_connection()
    conn.execute("UPDATE otp_tokens SET created_at = ?", ((datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),))
    conn.commit()
    conn.close()
    response = client.post("/auth/resend-verification", follow_redirects=False)
    assert response.status_code == 303
    new_code = clean_auth_db["verification"][1]
    assert new_code != old_code
    assert client.post("/verify-email", data={"otp": old_code}).status_code == 400
    assert client.post("/verify-email", data={"otp": new_code}, follow_redirects=False).status_code == 303


def test_unverified_login_redirects_and_verified_login_allows_access(clean_auth_db):
    register()
    login = client.post("/login", data={"username": "verify_user", "password": "password123"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/verify-email"
    assert "pocketsmart_session" not in login.cookies

    client.post("/verify-email", data={"otp": clean_auth_db["verification"][1]})
    login = client.post("/login", data={"username": "verify_user", "password": "password123"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/dashboard"
    assert client.get("/dashboard").status_code == 200


def test_invalid_credentials_are_generic(clean_auth_db):
    register()
    response = client.post("/login", data={"username": "nobody@example.com", "password": "wrong"})
    assert response.status_code == 400
    assert "Invalid email or password." in response.text
    assert "not found" not in response.text.lower()


def test_login_otp_enabled_and_disabled(clean_auth_db, monkeypatch):
    register()
    client.post("/verify-email", data={"otp": clean_auth_db["verification"][1]})
    monkeypatch.setenv("LOGIN_OTP_ENABLED", "true")
    login = client.post("/login", data={"username": "verify_user", "password": "password123"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/verify-login"
    login_verified = client.post("/verify-login", data={"otp": clean_auth_db["login"][1]}, follow_redirects=False)
    assert login_verified.status_code == 303
    assert login_verified.headers["location"] == "/dashboard"

    client.cookies.clear()
    monkeypatch.setenv("LOGIN_OTP_ENABLED", "false")
    login = client.post("/login", data={"username": "verify_user", "password": "password123"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/dashboard"


def test_protected_route_rejects_unverified_user(clean_auth_db):
    register()
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]
    assert client.get("/home-planner", follow_redirects=False).status_code == 302
    assert client.get("/party-planner", follow_redirects=False).status_code == 302
    assert client.get("/jewelry-planner", follow_redirects=False).status_code == 302
    assert client.get("/scan-product", follow_redirects=False).status_code == 302
