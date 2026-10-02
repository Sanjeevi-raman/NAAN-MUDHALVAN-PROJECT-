"""
PocketSmart AI - Budget Planning & Optimization Service
Calculates category allocations, total spend, travel additions,
remaining budget, and status indicators.
"""

from typing import Dict, Any, List
from models.recommendation import BudgetAllocation

def calculate_home_budget_allocation(total_budget: float) -> List[BudgetAllocation]:
    """
    Standard healthy interior budget allocation:
    - Furniture: ~50%
    - Lighting: ~20%
    - Ceiling Fans: ~15%
    - Decor: ~15%
    """
    allocations = [
        BudgetAllocation(
            category="Furniture",
            allocated_amount=round(total_budget * 0.50, 2),
            percentage=50.0,
            spent_amount=0.0
        ),
        BudgetAllocation(
            category="Lighting",
            allocated_amount=round(total_budget * 0.20, 2),
            percentage=20.0,
            spent_amount=0.0
        ),
        BudgetAllocation(
            category="Ceiling Fans",
            allocated_amount=round(total_budget * 0.15, 2),
            percentage=15.0,
            spent_amount=0.0
        ),
        BudgetAllocation(
            category="Decor",
            allocated_amount=round(total_budget * 0.15, 2),
            percentage=15.0,
            spent_amount=0.0
        ),
    ]
    return allocations

def calculate_party_budget_allocation(
    total_budget: float,
    accommodation_needed: bool = False
) -> List[BudgetAllocation]:
    """
    Standard event budget allocation:
    Without accommodation: Venue (35%), Catering (40%), Decoration (15%), Entertainment (10%)
    With accommodation: Venue (25%), Catering (35%), Accommodation (20%), Decoration (10%), Entertainment (10%)
    """
    if accommodation_needed:
        allocations = [
            BudgetAllocation(category="Catering", allocated_amount=round(total_budget * 0.35, 2), percentage=35.0, spent_amount=0.0),
            BudgetAllocation(category="Venue", allocated_amount=round(total_budget * 0.25, 2), percentage=25.0, spent_amount=0.0),
            BudgetAllocation(category="Accommodation", allocated_amount=round(total_budget * 0.20, 2), percentage=20.0, spent_amount=0.0),
            BudgetAllocation(category="Decoration", allocated_amount=round(total_budget * 0.10, 2), percentage=10.0, spent_amount=0.0),
            BudgetAllocation(category="Entertainment", allocated_amount=round(total_budget * 0.10, 2), percentage=10.0, spent_amount=0.0),
        ]
    else:
        allocations = [
            BudgetAllocation(category="Catering", allocated_amount=round(total_budget * 0.40, 2), percentage=40.0, spent_amount=0.0),
            BudgetAllocation(category="Venue", allocated_amount=round(total_budget * 0.35, 2), percentage=35.0, spent_amount=0.0),
            BudgetAllocation(category="Decoration", allocated_amount=round(total_budget * 0.15, 2), percentage=15.0, spent_amount=0.0),
            BudgetAllocation(category="Entertainment", allocated_amount=round(total_budget * 0.10, 2), percentage=10.0, spent_amount=0.0),
        ]
    return allocations

def calculate_jewelry_budget_allocation(total_budget: float) -> List[BudgetAllocation]:
    """
    Authentic Precious Jewelry allocation (Gold, Silver, Platinum, Diamond):
    - Necklace / Pendant / Chain: ~50%
    - Earrings / Studs: ~30%
    - Ring / Solitaire Band: ~20%
    """
    allocations = [
        BudgetAllocation(category="Necklace / Pendant", allocated_amount=round(total_budget * 0.50, 2), percentage=50.0, spent_amount=0.0),
        BudgetAllocation(category="Earrings / Studs", allocated_amount=round(total_budget * 0.30, 2), percentage=30.0, spent_amount=0.0),
        BudgetAllocation(category="Ring / Solitaire", allocated_amount=round(total_budget * 0.20, 2), percentage=20.0, spent_amount=0.0),
    ]
    return allocations

def evaluate_budget_status(total_budget: float, effective_total: float) -> str:
    """
    Determine if plan is within_budget, near_budget (95-100%), or over_budget.
    """
    if effective_total <= total_budget * 0.95:
        return "within_budget"
    elif effective_total <= total_budget:
        return "near_budget"
    else:
        return "over_budget"
