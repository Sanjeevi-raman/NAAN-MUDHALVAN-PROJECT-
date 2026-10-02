"""
PocketSmart AI - Home Interior Planner Routes
Handles inputs for room type, budget, quantities of furniture, lights, fans, and decor,
and renders structured budget recommendations.
"""

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from models.planner import HomePlannerInput
from services.auth_service import get_current_user_optional, get_current_user_required
from services.recommendation_service import generate_home_recommendations

router = APIRouter(tags=["Home Interior Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(request: Request):
    """Render the Home Interior Budget Planner interface."""
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+login+to+access+the+Home+Planner", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="home_planner.html", context={
        "user": user,
        "default_budget": 50000
    })

@router.post("/generate-home", response_class=HTMLResponse)
async def generate_home_plan(
    request: Request,
    total_budget: float = Form(...),
    room_type: str = Form(...),
    num_furniture: int = Form(default=2),
    num_lights: int = Form(default=4),
    num_fans: int = Form(default=1),
    num_decor: int = Form(default=2),
    style_preference: str = Form(default="Modern"),
    additional_notes: Optional[str] = Form(default="")
):
    """Process Home Interior inputs, validate constraints, and render recommendation cards."""
    user = get_current_user_required(request)

    # Input validation
    if total_budget <= 0:
        return templates.TemplateResponse(
            request=request,
            name="home_planner.html",
            context={"user": user, "error": "Budget must be greater than zero."},
            status_code=400
        )
    if total_budget > 100000000:
        return templates.TemplateResponse(
            request=request,
            name="home_planner.html",
            context={"user": user, "error": "Budget exceeds maximum threshold."},
            status_code=400
        )

    planner_input = HomePlannerInput(
        total_budget=total_budget,
        room_type=room_type.strip(),
        num_furniture=max(0, num_furniture),
        num_lights=max(0, num_lights),
        num_fans=max(0, num_fans),
        num_decor=max(0, num_decor),
        style_preference=style_preference.strip(),
        additional_notes=additional_notes.strip() if additional_notes else ""
    )

    summary, history_id = await generate_home_recommendations(
        planner_input=planner_input,
        user_id=user["id"]
    )

    # If requested as JSON (e.g. from fetch)
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse({
            "summary": summary.model_dump(),
            "history_id": history_id
        })

    return templates.TemplateResponse(request=request, name="home_recommendations.html", context={
        "user": user,
        "summary": summary,
        "history_id": history_id,
        "input": planner_input
    })
