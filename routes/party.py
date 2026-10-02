"""
PocketSmart AI - Party Budget Planner Routes
Handles event type, guest count, venue, catering, decoration, entertainment,
and browser geolocation for nearby-first venue search and 60 KM rule evaluation.
"""

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from models.planner import PartyPlannerInput
from services.auth_service import get_current_user_optional, get_current_user_required
from services.recommendation_service import generate_party_recommendations

router = APIRouter(tags=["Party Budget Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(request: Request):
    """Render the Party Budget Planner interface with geolocation support."""
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?error=Please+login+to+access+the+Party+Planner", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="party_planner.html", context={
        "user": user,
        "default_budget": 75000,
        "default_guests": 50
    })

@router.post("/generate-party", response_class=HTMLResponse)
async def generate_party_plan(
    request: Request,
    total_budget: float = Form(...),
    guest_count: int = Form(...),
    event_type: str = Form(...),
    venue_preference: str = Form(default="Banquet Hall"),
    catering_preference: str = Form(default="Buffet"),
    decoration_needed: bool = Form(default=True),
    entertainment_needed: bool = Form(default=True),
    accommodation_needed: bool = Form(default=False),
    user_latitude: Optional[float] = Form(default=None),
    user_longitude: Optional[float] = Form(default=None),
    travel_mode: str = Form(default="car"),
    additional_notes: Optional[str] = Form(default="")
):
    """Process event planning request with location intelligence."""
    user = get_current_user_required(request)

    # Input validations
    if total_budget <= 0:
        return templates.TemplateResponse(
            request=request,
            name="party_planner.html",
            context={"user": user, "error": "Budget must be greater than zero."},
            status_code=400
        )
    if guest_count <= 0:
        return templates.TemplateResponse(
            request=request,
            name="party_planner.html",
            context={"user": user, "error": "Guest count must be at least 1."},
            status_code=400
        )

    planner_input = PartyPlannerInput(
        total_budget=total_budget,
        guest_count=guest_count,
        event_type=event_type.strip(),
        venue_preference=venue_preference.strip(),
        catering_preference=catering_preference.strip(),
        decoration_needed=decoration_needed,
        entertainment_needed=entertainment_needed,
        accommodation_needed=accommodation_needed,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        travel_mode=travel_mode,
        additional_notes=additional_notes.strip() if additional_notes else ""
    )

    summary, history_id = await generate_party_recommendations(
        planner_input=planner_input,
        user_id=user["id"]
    )

    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse({
            "summary": summary.model_dump(),
            "history_id": history_id
        })

    return templates.TemplateResponse(request=request, name="party_recommendations.html", context={
        "user": user,
        "summary": summary,
        "history_id": history_id,
        "input": planner_input
    })
