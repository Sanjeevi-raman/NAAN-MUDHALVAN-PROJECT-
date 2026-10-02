"""
PocketSmart AI - Authentication & Session Routes
Provides endpoints for registration, login, logout, OAuth2 token issuance,
session information, and user session state retrieval.
"""

from fastapi import APIRouter, Request, Response, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import TypeAdapter, EmailStr, ValidationError
from datetime import datetime, timezone
import os
from typing import Optional

from database.database import get_db_connection
from models.user import UserRegister, UserLogin, UserResponse, TokenResponse, SessionInfoResponse
from services.auth_service import (
    hash_password,
    verify_password,
    create_session,
    delete_session,
    get_current_user_optional,
    get_current_user_required,
    SESSION_COOKIE_NAME,
    SESSION_LIFETIME_DAYS,
    PENDING_AUTH_COOKIE_NAME,
    create_otp_token,
    create_pending_auth_token,
    generate_otp,
    otp_send_allowed,
    read_pending_auth_token,
    verify_otp_token,
)
from services.email_service import EmailDeliveryError, send_login_otp, send_verification_otp

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")
EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
LOGIN = "LOGIN"


def _mask_email(email: str) -> str:
    local, domain = email.split("@", 1)
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}{'*' * max(2, len(local) - len(visible))}@{domain}"


def _valid_email(email: str) -> Optional[str]:
    try:
        return str(TypeAdapter(EmailStr).validate_python(email.strip().lower()))
    except ValidationError:
        return None


def _user_by_id(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def _user_by_login(login: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (login, login))
    row = cursor.fetchone()
    conn.close()
    return row


def _set_pending_cookie(response: RedirectResponse, user_id: int, purpose: str) -> None:
    response.set_cookie(
        key=PENDING_AUTH_COOKIE_NAME,
        value=create_pending_auth_token(user_id, purpose),
        max_age=600,
        httponly=True,
        samesite="lax",
    )


def _pending_user(request: Request, purpose: str, email: Optional[str] = None):
    user_id = read_pending_auth_token(request.cookies.get(PENDING_AUTH_COOKIE_NAME), purpose)
    if user_id:
        return _user_by_id(user_id)
    if email:
        clean_email = _valid_email(email)
        if clean_email:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (clean_email,))
            row = cursor.fetchone()
            conn.close()
            return row
    return None


def _issue_otp(user_row, purpose: str) -> None:
    otp, _ = create_otp_token(user_row["id"], purpose)
    if purpose == EMAIL_VERIFICATION:
        send_verification_otp(user_row["email"], otp)
    else:
        send_login_otp(user_row["email"], otp)


def _verify_context(user_row, error: Optional[str] = None):
    return {
        "user": None,
        "email": user_row["email"] if user_row else "",
        "masked_email": _mask_email(user_row["email"]) if user_row else "your email address",
        "error": error,
    }

# =====================================================================
# HTML PAGES
# =====================================================================

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page. Redirect to dashboard if already logged in."""
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None, "error": None})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Render login page. Redirect to dashboard if already logged in."""
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "error": error})

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, error: Optional[str] = None):
    user_row = _pending_user(request, EMAIL_VERIFICATION, request.query_params.get("email"))
    return templates.TemplateResponse(request=request, name="verify_email.html", context=_verify_context(user_row, error))

@router.get("/verify-login", response_class=HTMLResponse)
async def verify_login_page(request: Request, error: Optional[str] = None):
    user_row = _pending_user(request, LOGIN)
    return templates.TemplateResponse(request=request, name="verify_login.html", context=_verify_context(user_row, error))

# =====================================================================
# FORM / API ACTIONS
# =====================================================================

@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None)
):
    """Register a new user account with duplicate detection and password hashing."""
    clean_username = username.strip().lower()
    clean_email = _valid_email(email)

    if len(clean_username) < 3:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username must be at least 3 characters.", "user": None},
            status_code=400
        )
    if not clean_email:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Enter a valid email address.", "user": None},
            status_code=400
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Password must be at least 6 characters.", "user": None},
            status_code=400
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check for existing username or email
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (clean_username, clean_email))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username or email is already registered.", "user": None},
            status_code=400
        )

    hashed = hash_password(password)
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, full_name, email_verified)
        VALUES (?, ?, ?, ?, 0)
    """, (clean_username, clean_email, hashed, full_name.strip() if full_name else None))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    user_row = _user_by_id(user_id)
    redirect = RedirectResponse(url="/verify-email", status_code=status.HTTP_303_SEE_OTHER)
    _set_pending_cookie(redirect, user_id, EMAIL_VERIFICATION)
    try:
        _issue_otp(user_row, EMAIL_VERIFICATION)
    except EmailDeliveryError:
        redirect = RedirectResponse(url="/verify-email?error=We+couldn't+send+the+verification+code+right+now.+Please+try+again.", status_code=status.HTTP_303_SEE_OTHER)
        _set_pending_cookie(redirect, user_id, EMAIL_VERIFICATION)
    return redirect

@router.post("/login")
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Authenticate user with username and password, handle invalid credentials."""
    clean_username = username.strip().lower()
    user_row = _user_by_login(clean_username)

    if not user_row or not verify_password(password, user_row["hashed_password"]):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid email or password.", "user": None},
            status_code=400
        )

    if not bool(user_row["email_verified"]):
        redirect = RedirectResponse(url="/verify-email", status_code=status.HTTP_303_SEE_OTHER)
        _set_pending_cookie(redirect, user_row["id"], EMAIL_VERIFICATION)
        allowed, _ = otp_send_allowed(user_row["id"], EMAIL_VERIFICATION)
        if allowed:
            try:
                _issue_otp(user_row, EMAIL_VERIFICATION)
            except EmailDeliveryError:
                return templates.TemplateResponse(request=request, name="login.html", context={"error": "We couldn't send the verification code right now. Please try again.", "user": None}, status_code=503)
        return redirect

    if os.getenv("LOGIN_OTP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        allowed, _ = otp_send_allowed(user_row["id"], LOGIN)
        if not allowed:
            return templates.TemplateResponse(request=request, name="login.html", context={"error": "Please wait before requesting another login code.", "user": None}, status_code=429)
        try:
            _issue_otp(user_row, LOGIN)
        except EmailDeliveryError:
            return templates.TemplateResponse(request=request, name="login.html", context={"error": "We couldn't send the verification code right now. Please try again.", "user": None}, status_code=503)
        redirect = RedirectResponse(url="/verify-login", status_code=status.HTTP_303_SEE_OTHER)
        _set_pending_cookie(redirect, user_row["id"], LOGIN)
        return redirect

    token = create_session(user_row["id"])
    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_LIFETIME_DAYS * 86400,
        httponly=True,
        samesite="lax"
    )
    return redirect

@router.post("/verify-email")
async def verify_email(request: Request, otp: str = Form(...)):
    user_row = _pending_user(request, EMAIL_VERIFICATION)
    result = verify_otp_token(user_row["id"], EMAIL_VERIFICATION, otp) if user_row else "invalid"
    if result == "success":
        conn = get_db_connection()
        conn.execute("UPDATE users SET email_verified = 1, email_verified_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), user_row["id"]))
        conn.commit()
        conn.close()
        session_token = create_session(user_row["id"])
        redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        redirect.set_cookie(key=SESSION_COOKIE_NAME, value=session_token, max_age=SESSION_LIFETIME_DAYS * 86400, httponly=True, samesite="lax")
        redirect.delete_cookie(PENDING_AUTH_COOKIE_NAME)
        return redirect
    error = "This code has expired. Request a new code." if result == "expired" else "Invalid verification code. Please try again."
    return templates.TemplateResponse(request=request, name="verify_email.html", context=_verify_context(user_row, error), status_code=400)

@router.post("/auth/resend-verification")
async def resend_verification(request: Request, email: Optional[str] = Form(None)):
    user_row = _pending_user(request, EMAIL_VERIFICATION, email)
    redirect = RedirectResponse(url="/verify-email", status_code=status.HTTP_303_SEE_OTHER)
    if user_row:
        _set_pending_cookie(redirect, user_row["id"], EMAIL_VERIFICATION)
        if not bool(user_row["email_verified"]):
            allowed, remaining = otp_send_allowed(user_row["id"], EMAIL_VERIFICATION)
            if not allowed:
                message = "Please wait before requesting another code." if remaining else "Too many requests. Please try again later."
                return RedirectResponse(url=f"/verify-email?error={message.replace(' ', '+')}", status_code=status.HTTP_303_SEE_OTHER, headers={"Set-Cookie": redirect.headers.get("set-cookie", "")})
            try:
                _issue_otp(user_row, EMAIL_VERIFICATION)
            except EmailDeliveryError:
                return RedirectResponse(url="/verify-email?error=We+couldn't+send+the+verification+code+right+now.+Please+try+again.", status_code=status.HTTP_303_SEE_OTHER, headers={"Set-Cookie": redirect.headers.get("set-cookie", "")})
    return redirect

@router.post("/verify-login")
async def verify_login(request: Request, otp: str = Form(...)):
    user_row = _pending_user(request, LOGIN)
    result = verify_otp_token(user_row["id"], LOGIN, otp) if user_row else "invalid"
    if result == "success":
        token = create_session(user_row["id"])
        redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        redirect.set_cookie(key=SESSION_COOKIE_NAME, value=token, max_age=SESSION_LIFETIME_DAYS * 86400, httponly=True, samesite="lax")
        redirect.delete_cookie(PENDING_AUTH_COOKIE_NAME)
        return redirect
    error = "This code has expired. Request a new code." if result == "expired" else "Invalid login code. Please try again."
    return templates.TemplateResponse(request=request, name="verify_login.html", context=_verify_context(user_row, error), status_code=400)

@router.post("/auth/resend-login")
async def resend_login(request: Request):
    user_row = _pending_user(request, LOGIN)
    redirect = RedirectResponse(url="/verify-login", status_code=status.HTTP_303_SEE_OTHER)
    if user_row:
        _set_pending_cookie(redirect, user_row["id"], LOGIN)
        allowed, remaining = otp_send_allowed(user_row["id"], LOGIN)
        if not allowed:
            message = "Please wait before requesting another code." if remaining else "Too many requests. Please try again later."
            return RedirectResponse(url=f"/verify-login?error={message.replace(' ', '+')}", status_code=status.HTTP_303_SEE_OTHER, headers={"Set-Cookie": redirect.headers.get("set-cookie", "")})
        try:
            _issue_otp(user_row, LOGIN)
        except EmailDeliveryError:
            return RedirectResponse(url="/verify-login?error=We+couldn't+send+the+verification+code+right+now.+Please+try+again.", status_code=status.HTTP_303_SEE_OTHER, headers={"Set-Cookie": redirect.headers.get("set-cookie", "")})
    return redirect

@router.post("/logout")
async def logout_user(request: Request):
    """Securely log out user and invalidate session."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        delete_session(token)
    
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(SESSION_COOKIE_NAME)
    return redirect

@router.get("/logout")
async def logout_user_get(request: Request):
    """Support GET /logout for simple anchor links."""
    return await logout_user(request)

# =====================================================================
# JSON API ENDPOINTS
# =====================================================================

@router.post("/token", response_model=TokenResponse)
async def api_token_login(login_data: UserLogin):
    """Issue API bearer token for programmatic API access."""
    clean_username = login_data.username.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, hashed_password, full_name, created_at, email_verified FROM users WHERE username = ?", (clean_username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not verify_password(login_data.password, row["hashed_password"]) or not bool(row["email_verified"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    if os.getenv("LOGIN_OTP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Login OTP is required for this account")

    token = create_session(row["id"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            created_at=row["created_at"],
            email_verified=bool(row["email_verified"])
        )
    )

@router.get("/session-info")
async def session_info(request: Request):
    """Check current authentication status and user profile."""
    user = get_current_user_optional(request)
    if not user:
        return JSONResponse({"authenticated": False, "user": None})
    return JSONResponse({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "email_verified": user["email_verified"]
        }
    })

@router.get("/session-data")
async def session_data(request: Request):
    """Retrieve user-specific session personalization data."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return JSONResponse({
        "user_id": user["id"],
        "username": user["username"],
        "session_data": user["session_data"]
    })
