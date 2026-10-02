"""
PocketSmart AI - Landing, Dashboard & Recommendation Details Routes
Renders the primary landing presentation, user dashboard,
and granular recommendation inspection views.
"""

from fastapi import APIRouter, Request, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import json

from database.database import get_db_connection
from services.auth_service import get_current_user_optional, get_current_user_required

router = APIRouter(tags=["Recommendations & Dashboard"])
templates = Jinja2Templates(directory="templates")

# =====================================================================
# LANDING PAGE
# =====================================================================

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Renders PocketSmart AI landing page with brand hero, 3 budget planners,
    key benefits, product scan feature preview, and CTA.
    """
    user = get_current_user_optional(request)
    return templates.TemplateResponse(request=request, name="index.html", context={
        "user": user
    })

# =====================================================================
# DASHBOARD
# =====================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Renders user dashboard with welcome greeting, quick-access cards
    to the 3 budget planners + Scan Product, recent activity summary,
    and cumulative statistics.
    """
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+login+to+access+your+dashboard", status_code=status.HTTP_302_FOUND)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Cumulative stats
    cursor.execute("""
        SELECT COUNT(id) as total_plans, COALESCE(SUM(total_budget), 0) as total_budget_sum
        FROM recommendation_histories
        WHERE user_id = ?
    """, (user["id"],))
    stats_row = cursor.fetchone()
    total_plans = stats_row["total_plans"] if stats_row else 0
    total_budget_sum = stats_row["total_budget_sum"] if stats_row else 0.0

    # Total scans & savings
    cursor.execute("""
        SELECT COUNT(id) as total_scans, COALESCE(SUM(possible_saving), 0) as total_savings
        FROM product_scans
        WHERE user_id = ?
    """, (user["id"],))
    scan_stats = cursor.fetchone()
    total_scans = scan_stats["total_scans"] if scan_stats else 0
    total_savings = scan_stats["total_savings"] if scan_stats else 0.0

    # Recent plans
    cursor.execute("""
        SELECT h.*, COUNT(r.id) as item_count
        FROM recommendation_histories h
        LEFT JOIN recommendation_results r ON h.id = r.history_id
        WHERE h.user_id = ?
        GROUP BY h.id
        ORDER BY h.created_at DESC
        LIMIT 5
    """, (user["id"],))
    recent_plans = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "user": user,
        "total_plans": total_plans,
        "total_budget_sum": total_budget_sum,
        "total_scans": total_scans,
        "total_savings": total_savings,
        "recent_plans": recent_plans
    })

# =====================================================================
# RECOMMENDATION DETAILS
# =====================================================================

@router.get("/recommendations-details", response_class=HTMLResponse)
async def recommendation_details_page(
    request: Request,
    id: Optional[int] = Query(None, description="Specific recommendation item ID"),
    history_id: Optional[int] = Query(None, description="Entire plan history ID")
):
    """
    Renders detailed information for an individual recommendation item
    or displays the complete itemized breakdown of a saved plan.
    """
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+login+to+view+recommendation+details", status_code=status.HTTP_302_FOUND)

    conn = get_db_connection()
    cursor = conn.cursor()

    item = None
    plan = None
    items = []

    # 1. If single item requested
    if id:
        cursor.execute("""
            SELECT r.*, h.planner_type, h.total_budget, h.user_id
            FROM recommendation_results r
            JOIN recommendation_histories h ON r.history_id = h.id
            WHERE r.id = ? AND h.user_id = ?
        """, (id, user["id"]))
        item = cursor.fetchone()

    # 2. If plan history requested
    if history_id:
        cursor.execute("""
            SELECT * FROM recommendation_histories
            WHERE id = ? AND user_id = ?
        """, (history_id, user["id"]))
        plan = cursor.fetchone()

        if plan:
            cursor.execute("""
                SELECT * FROM recommendation_results
                WHERE history_id = ?
                ORDER BY id ASC
            """, (history_id,))
            items = cursor.fetchall()

    conn.close()

    if not item and not plan:
        raise HTTPException(status_code=404, detail="Recommendation details not found or access denied.")

    return templates.TemplateResponse(request=request, name="recommendation_details.html", context={
        "user": user,
        "item": item,
        "plan": plan,
        "items": items
    })
