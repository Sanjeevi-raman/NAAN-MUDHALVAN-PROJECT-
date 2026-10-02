"""
Planner input models for Home, Party, and Jewelry planners.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class HomePlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0, le=100000000, description="Total budget in INR")
    room_type: str = Field(..., min_length=2, max_length=50, description="Living Room, Kitchen, Bedroom, etc.")
    num_furniture: int = Field(default=2, ge=0, le=100, description="Number of furniture items")
    num_lights: int = Field(default=4, ge=0, le=100, description="Number of lighting fixtures")
    num_fans: int = Field(default=1, ge=0, le=50, description="Number of ceiling fans")
    num_decor: int = Field(default=2, ge=0, le=100, description="Number of decor items")
    style_preference: Optional[str] = Field(default="Modern", description="Modern, Minimalist, Traditional, etc.")
    additional_notes: Optional[str] = Field(default="", max_length=1000)

class PartyPlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0, le=100000000, description="Total budget in INR")
    guest_count: int = Field(..., ge=1, le=10000, description="Total expected guests")
    event_type: str = Field(..., min_length=2, max_length=50, description="Birthday, Wedding, Corporate, etc.")
    venue_preference: Optional[str] = Field(default="Banquet Hall", description="Banquet, Lawn, Restaurant, Hotel")
    catering_preference: Optional[str] = Field(default="Buffet", description="Buffet, Finger Food, Traditional")
    decoration_needed: bool = Field(default=True)
    entertainment_needed: bool = Field(default=True)
    accommodation_needed: bool = Field(default=False)
    user_latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    user_longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    travel_mode: Optional[str] = Field(default="car", description="car, bike, public")
    additional_notes: Optional[str] = Field(default="", max_length=1000)

class JewelryPlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0, le=100000000, description="Total budget in INR")
    occasion: str = Field(..., min_length=2, max_length=50, description="Wedding, Festival, Party, Casual")
    style_preference: Optional[str] = Field(default="Contemporary", description="Traditional, Contemporary, Minimalist")
    precious_metal: Optional[str] = Field(default="Gold", description="Gold, Silver, Platinum, Diamond, or All Precious")
    location: Optional[str] = Field(default="Nearby", description="City or locality for nearby certified jeweler showrooms")
    jewelry_types: Optional[List[str]] = Field(default_factory=lambda: ["Necklace", "Earrings", "Ring"])
    outfit_description: Optional[str] = Field(default="", max_length=1000)
