"""
PocketSmart AI - Jewelry Budget Planner Routes
Supports text-only and multimodal outfit image + text inputs to generate
personalized, occasion-aware jewelry recommendations.
"""

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List

from models.planner import JewelryPlannerInput
from services.auth_service import get_current_user_optional, get_current_user_required
from services.recommendation_service import generate_jewelry_recommendations

router = APIRouter(tags=["Jewelry Budget Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request):
    """Render the Jewelry Budget Planner form with optional outfit image upload."""
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+login+to+access+the+Jewelry+Planner", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="jewelry_planner.html", context={
        "user": user,
        "default_budget": 15000
    })

@router.post("/generate-jewelry", response_class=HTMLResponse)
async def generate_jewelry_plan(
    request: Request,
    total_budget: float = Form(...),
    occasion: str = Form(...),
    style_preference: str = Form(default="Contemporary"),
    precious_metal: str = Form(default="Gold"),
    location: Optional[str] = Form(default="Nearby"),
    outfit_description: Optional[str] = Form(default=""),
    outfit_image: Optional[UploadFile] = File(None)
):
    """Process jewelry styling request using text or multimodal image input for real precious jewels."""
    user = get_current_user_required(request)

    if total_budget <= 0:
        return templates.TemplateResponse(
            request=request,
            name="jewelry_planner.html",
            context={"user": user, "error": "Budget must be greater than zero."},
            status_code=400
        )

    image_bytes = None
    image_mime = None
    if outfit_image and outfit_image.filename:
        image_bytes = await outfit_image.read()
        image_mime = outfit_image.content_type or "image/jpeg"

    planner_input = JewelryPlannerInput(
        total_budget=total_budget,
        occasion=occasion.strip(),
        style_preference=style_preference.strip(),
        precious_metal=precious_metal.strip(),
        location=location.strip() if location else "Nearby",
        jewelry_types=["Necklace", "Earrings", "Ring"],
        outfit_description=outfit_description.strip() if outfit_description else ""
    )

    summary, history_id = await generate_jewelry_recommendations(
        planner_input=planner_input,
        outfit_image_bytes=image_bytes,
        outfit_image_mime=image_mime,
        user_id=user["id"]
    )

    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse({
            "summary": summary.model_dump(),
            "history_id": history_id
        })

    return templates.TemplateResponse(request=request, name="jewelry_recommendations.html", context={
        "user": user,
        "summary": summary,
        "history_id": history_id,
        "input": planner_input
    })
