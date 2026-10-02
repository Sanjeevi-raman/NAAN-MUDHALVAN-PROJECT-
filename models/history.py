"""
History models for recommendation plans and product scans.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HistoryItemResponse(BaseModel):
    id: int
    user_id: int
    planner_type: str
    total_budget: float
    allocated_spend: float
    estimated_travel: float
    remaining_budget: float
    status: str
    summary_text: Optional[str] = None
    created_at: str
    item_count: int = 0

class OnlinePriceItem(BaseModel):
    platform: str
    product_title: str
    price: float
    shipping: float = 0.0
    total_payable: float
    availability: str = "In Stock"
    url: str
    is_live: bool = False
    timestamp: str

class ProductScanResult(BaseModel):
    product_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    match_confidence: str  # "Exact Match", "Likely Match", "Possible Match", "Unable to Identify"
    visible_specs: List[str] = []
    local_price: float
    online_prices: List[OnlinePriceItem] = []
    lowest_observed_price: Optional[float] = None
    lowest_platform: Optional[str] = None
    price_difference: Optional[float] = None
    possible_saving: Optional[float] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    is_demo: bool = False

class ProductScanHistoryItem(BaseModel):
    id: int
    user_id: int
    product_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    match_confidence: str
    category: Optional[str] = None
    local_price: float
    lowest_online_price: Optional[float] = None
    price_difference: Optional[float] = None
    possible_saving: Optional[float] = None
    online_prices: List[OnlinePriceItem] = []
    image_path: Optional[str] = None
    created_at: str
