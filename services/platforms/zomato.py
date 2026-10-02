"""
Zomato Platform Adapter
Handles Zomato restaurant dining, party venue, and catering search URLs.
"""

import urllib.parse
from typing import Dict, Any, List

PLATFORM_NAME = "Zomato"
BASE_SEARCH_URL = "https://www.zomato.com"

def get_zomato_search_url(query: str, city: str = "india") -> str:
    """Generate a verified, actionable Zomato search URL."""
    encoded_query = urllib.parse.quote_plus(query.strip())
    encoded_city = urllib.parse.quote_plus(city.strip().lower())
    return f"{BASE_SEARCH_URL}/{encoded_city}/restaurants?q={encoded_query}"
