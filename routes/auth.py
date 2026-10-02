"""
PocketSmart AI - Authentication & Session Routes
Provides endpoints for registration, login, logout, OAuth2 token issuance,
session information, and user session state retrieval.
"""

from fastapi import APIRouter, Request, Response, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
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
    SESSION_LIFETIME_DAYS
)

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

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

# =====================================================================
# FORM / API ACTIONS
# =====================================================================

@router.post("/register")
async def register_user(
    request: Request,
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None)
):
    """Register a new user account with duplicate detection and password hashing."""
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()

    if len(clean_username) < 3:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username must be at least 3 characters.", "user": None},
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
        INSERT INTO users (username, email, hashed_password, full_name)
        VALUES (?, ?, ?, ?)
    """, (clean_username, clean_email, hashed, full_name.strip() if full_name else None))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    # Create session and set cookie
    token = create_session(user_id)
    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_LIFETIME_DAYS * 86400,
        httponly=True,
        samesite="lax"
    )
    return redirect

@router.post("/login")
async def login_user(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """Authenticate user with username and password, handle invalid credentials."""
    clean_username = username.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, hashed_password, full_name FROM users WHERE username = ?", (clean_username,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row or not verify_password(password, user_row["hashed_password"]):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid username or password.", "user": None},
            status_code=400
        )

    # Valid login: create session
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
    cursor.execute("SELECT id, username, email, hashed_password, full_name, created_at FROM users WHERE username = ?", (clean_username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not verify_password(login_data.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    token = create_session(row["id"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            created_at=row["created_at"]
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
            "full_name": user["full_name"]
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
