"""
Swiggy Platform Adapter
Handles Swiggy food, bulk meal, and party catering search queries.
"""

import urllib.parse
from typing import Dict, Any, List

PLATFORM_NAME = "Swiggy"
BASE_SEARCH_URL = "https://www.swiggy.com/search"

def get_swiggy_search_url(query: str) -> str:
    """Generate a verified, actionable Swiggy search URL."""
    encoded_query = urllib.parse.quote_plus(query.strip())
    return f"{BASE_SEARCH_URL}?query={encoded_query}"
