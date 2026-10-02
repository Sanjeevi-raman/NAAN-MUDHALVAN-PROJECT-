"""
PocketSmart AI - History Routes
Provides user-isolated history of generated plans (Home, Party, Jewelry)
and product price comparisons with options to reopen and review details.
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import json

from database.database import get_db_connection
from services.auth_service import get_current_user_optional, get_current_user_required

router = APIRouter(tags=["History"])
templates = Jinja2Templates(directory="templates")

@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, filter_type: Optional[str] = "all"):
    """Render user recommendation history and price scan log with user-level isolation."""
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+login+to+view+your+history", status_code=status.HTTP_302_FOUND)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Query recommendation histories for current user
    if filter_type and filter_type.lower() in ["home", "party", "jewelry"]:
        cursor.execute("""
            SELECT h.*, COUNT(r.id) as item_count
            FROM recommendation_histories h
            LEFT JOIN recommendation_results r ON h.id = r.history_id
            WHERE h.user_id = ? AND h.planner_type = ?
            GROUP BY h.id
            ORDER BY h.created_at DESC
        """, (user["id"], filter_type.lower()))
    else:
        cursor.execute("""
            SELECT h.*, COUNT(r.id) as item_count
            FROM recommendation_histories h
            LEFT JOIN recommendation_results r ON h.id = r.history_id
            WHERE h.user_id = ?
            GROUP BY h.id
            ORDER BY h.created_at DESC
        """, (user["id"],))
    
    plans = cursor.fetchall()

    # Query product scans for current user
    cursor.execute("""
        SELECT * FROM product_scans
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 25
    """, (user["id"],))
    scans = cursor.fetchall()

    parsed_scans = []
    for s in scans:
        parsed_scans.append({
            "id": s["id"],
            "product_name": s["product_name"],
            "brand": s["brand"],
            "model": s["model"],
            "match_confidence": s["match_confidence"],
            "local_price": s["local_price"],
            "lowest_online_price": s["lowest_online_price"],
            "possible_saving": s["possible_saving"],
            "image_path": s["image_path"],
            "created_at": s["created_at"],
            "online_prices": json.loads(s["online_prices_json"] or "[]")
        })

    conn.close()

    return templates.TemplateResponse(request=request, name="history.html", context={
        "user": user,
        "plans": plans,
        "scans": parsed_scans,
        "current_filter": filter_type
    })

@router.get("/api/history")
async def api_history(request: Request):
    """Return JSON history for programmatic access."""
    user = get_current_user_required(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM recommendation_histories
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return JSONResponse([dict(r) for r in rows])
