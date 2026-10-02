"""
PocketSmart AI - Location & Travel Routes
Provides endpoints for nearby venue discovery, route distance estimation,
and transit cost breakdowns across transport modes.
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from services.location_service import search_nearby_venues, calculate_haversine_distance, is_within_60km
from services.travel_service import get_travel_breakdown, estimate_travel_expense, estimate_travel_time_minutes

router = APIRouter(prefix="/api", tags=["Location & Travel"])

class NearbySearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    event_type: Optional[str] = "Birthday"
    guest_count: Optional[int] = 50
    budget: Optional[float] = 50000.0
    travel_mode: Optional[str] = "car"

class TravelEstimateRequest(BaseModel):
    distance_km: float = Field(..., ge=0.0)
    mode: Optional[str] = "car"

@router.post("/location/nearby")
async def get_nearby_venues_api(data: NearbySearchRequest):
    """
    Search nearby venues within 60 KM rule.
    Computes distance, travel duration, travel expense, and Google Maps links.
    """
    venues = await search_nearby_venues(
        user_lat=data.latitude,
        user_lon=data.longitude,
        event_type=data.event_type or "Party",
        guest_count=data.guest_count or 50,
        budget=data.budget or 50000.0,
        travel_mode=data.travel_mode or "car"
    )
    return JSONResponse({
        "status": "success",
        "radius_rule_km": 60.0,
        "count": len(venues),
        "venues": venues
    })

@router.post("/travel/estimate")
async def get_travel_estimate_api(data: TravelEstimateRequest):
    """Calculate multi-modal transit cost breakdown for given distance."""
    breakdown = get_travel_breakdown(data.distance_km)
    return JSONResponse(breakdown)
