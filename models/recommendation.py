"""
Structured recommendation models for products and places.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RecommendationItem(BaseModel):
    name: str = Field(..., description="Product or place name")
    category: str = Field(..., description="Lighting, Furniture, Venue, Catering, Jewelry, etc.")
    description: Optional[str] = Field(default="", description="Detailed description")
    price: float = Field(..., ge=0, description="Unit price or base service fee in INR")
    quantity: int = Field(default=1, ge=1, description="Quantity")
    total_price: float = Field(..., ge=0, description="Total item price (price * quantity)")
    platform: str = Field(..., description="Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, Local")
    url: str = Field(..., description="Actionable valid URL (Product or Search link)")
    reason: Optional[str] = Field(default="", description="Why this fits user's budget and taste")
    
    # Location & Travel Fields (when applicable)
    distance_km: Optional[float] = Field(default=None, description="Distance from user in KM")
    travel_time_minutes: Optional[int] = Field(default=None, description="Travel time in minutes")
    travel_cost_estimate: Optional[float] = Field(default=None, description="Estimated travel cost in INR")
    effective_total_cost: Optional[float] = Field(default=None, description="Service cost + travel estimate")
    rating: Optional[float] = Field(default=None, description="Customer rating (e.g. 4.3)")
    review_count: Optional[int] = Field(default=None, description="Number of reviews")
    location: Optional[str] = Field(default=None, description="Physical address or neighborhood")
    google_maps_url: Optional[str] = Field(default=None, description="Google Maps search/place link")
    is_nearby: Optional[bool] = Field(default=True, description="True if distance <= 60km")
    purity_badge: Optional[str] = Field(default=None, description="BIS 916 Hallmark, Pt 950, 925 Silver, IGI Diamond")
    is_mock: bool = Field(default=False, description="True if using mock/demo data")

class BudgetAllocation(BaseModel):
    category: str
    allocated_amount: float
    percentage: float
    spent_amount: float

class RecommendationSummary(BaseModel):
    planner_type: str
    total_budget: float
    total_spend: float
    total_travel_estimate: float
    effective_total: float
    remaining_budget: float
    budget_status: str  # "within_budget", "near_budget", "over_budget"
    allocations: List[BudgetAllocation] = []
    items: List[RecommendationItem]
    ai_summary: Optional[str] = None
    nearby_shops: Optional[List[Dict[str, Any]]] = Field(default=None, description="Certified jewel shops / showrooms")
    is_demo: bool = False

class RecommendationDetailResponse(BaseModel):
    id: int
    history_id: int
    item: RecommendationItem
    created_at: str
