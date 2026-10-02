"""
PocketSmart AI - Travel Cost & Time Estimation Service
Estimates travel costs and transit durations across car, bike, and public transport modes.
Estimates are calculated transparently using configurable rates.
"""

import os
from typing import Dict, Any, Optional

# Load configurable travel costs from environment
CAR_COST_PER_KM = float(os.getenv("CAR_COST_PER_KM", "12.0"))
BIKE_COST_PER_KM = float(os.getenv("BIKE_COST_PER_KM", "4.5"))
PUBLIC_TRANSPORT_PER_KM = float(os.getenv("PUBLIC_TRANSPORT_ESTIMATE", "2.0"))

# Average urban/suburban speeds in km/h for realistic travel time estimation
SPEEDS_KMH = {
    "car": 28.0,
    "bike": 32.0,
    "public": 20.0
}

def estimate_travel_expense(distance_km: float, mode: str = "car") -> float:
    """
    Calculate estimated round-trip or single travel expense in INR.
    Uses configurable per-km rates. Returns a rounded estimate.
    """
    if distance_km <= 0:
        return 0.0
    
    clean_mode = mode.lower().strip()
    if clean_mode == "bike":
        rate = BIKE_COST_PER_KM
    elif clean_mode in ["public", "bus", "train", "metro"]:
        rate = PUBLIC_TRANSPORT_PER_KM
    else:
        rate = CAR_COST_PER_KM

    # Round trip factor for events (going and returning)
    total_km = distance_km * 2.0
    estimated_cost = round(total_km * rate, 2)
    return estimated_cost

def estimate_travel_time_minutes(distance_km: float, mode: str = "car") -> int:
    """
    Estimate one-way travel duration in minutes based on realistic average city transit speed.
    """
    if distance_km <= 0:
        return 0
    
    clean_mode = mode.lower().strip()
    speed = SPEEDS_KMH.get(clean_mode, SPEEDS_KMH["car"])
    
    # Time in hours = distance / speed
    hours = distance_km / speed
    minutes = int(round(hours * 60))
    # Minimum 5 minutes buffer for parking/traffic
    return max(5, minutes)

def get_travel_breakdown(distance_km: float) -> Dict[str, Any]:
    """
    Return comprehensive travel estimates across all supported transport modes.
    """
    return {
        "distance_km": round(distance_km, 2),
        "car": {
            "rate_per_km": CAR_COST_PER_KM,
            "estimated_roundtrip_cost": estimate_travel_expense(distance_km, "car"),
            "one_way_duration_minutes": estimate_travel_time_minutes(distance_km, "car")
        },
        "bike": {
            "rate_per_km": BIKE_COST_PER_KM,
            "estimated_roundtrip_cost": estimate_travel_expense(distance_km, "bike"),
            "one_way_duration_minutes": estimate_travel_time_minutes(distance_km, "bike")
        },
        "public_transit": {
            "rate_per_km": PUBLIC_TRANSPORT_PER_KM,
            "estimated_roundtrip_cost": estimate_travel_expense(distance_km, "public"),
            "one_way_duration_minutes": estimate_travel_time_minutes(distance_km, "public")
        },
        "disclaimer": "Travel expenses and times are transparent estimates based on average rates and urban traffic conditions."
    }
