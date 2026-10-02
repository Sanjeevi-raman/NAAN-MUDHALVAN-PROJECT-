"""
PocketSmart AI - Product Price Scanner Routes
Provides camera capture, file upload, multimodal product recognition,
and in-store physical price vs online price comparison.
"""

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import json

from database.database import get_db_connection
from models.history import ProductScanResult
from services.auth_service import get_current_user_optional, get_current_user_required
from services.product_scan_service import process_product_scan

router = APIRouter(tags=["Product Price Scanner"])
templates = Jinja2Templates(directory="templates")

@router.get("/scan-product", response_class=HTMLResponse)
async def scan_product_page(request: Request):
    """Render the Scan Product interface with live camera and upload controls."""
    user = get_current_user_optional(request)
    return templates.TemplateResponse(request=request, name="scan_product.html", context={
        "user": user,
        "scan_result": None,
        "error": None
    })

@router.post("/scan-product", response_class=HTMLResponse)
async def execute_product_scan(
    request: Request,
    local_price: float = Form(...),
    manual_product_name: Optional[str] = Form(None),
    product_image: Optional[UploadFile] = File(None)
):
    """Analyze product image, identify specifications, compare with online market prices."""
    user = get_current_user_optional(request)
    user_id = user["id"] if user else None

    if local_price <= 0:
        return templates.TemplateResponse(
            request=request,
            name="scan_product.html",
            context={
                "user": user,
                "scan_result": None,
                "error": "Local store price must be greater than zero."
            },
            status_code=400
        )

    scan_result = await process_product_scan(
        image_file=product_image,
        local_price=local_price,
        manual_product_name=manual_product_name,
        user_id=user_id
    )

    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(scan_result.model_dump())

    return templates.TemplateResponse(request=request, name="scan_product.html", context={
        "user": user,
        "scan_result": scan_result,
        "error": None
    })

@router.get("/api/scan-history")
async def get_scan_history_api(request: Request):
    """Return logged-in user's previous product price scans."""
    user = get_current_user_required(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM product_scans
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "product_name": r["product_name"],
            "brand": r["brand"],
            "model": r["model"],
            "match_confidence": r["match_confidence"],
            "local_price": r["local_price"],
            "lowest_online_price": r["lowest_online_price"],
            "possible_saving": r["possible_saving"],
            "online_prices": json.loads(r["online_prices_json"] or "[]"),
            "image_path": r["image_path"],
            "created_at": r["created_at"]
        })
    return JSONResponse(results)
