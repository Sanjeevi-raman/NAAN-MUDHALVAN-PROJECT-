"""
OYO Platform Adapter
Handles OYO accommodation searches when party planning requires guest rooms.
"""

import urllib.parse
from typing import Dict, Any, List

PLATFORM_NAME = "OYO"
BASE_SEARCH_URL = "https://www.oyorooms.com"

def get_oyo_search_url(city_or_location: str = "india") -> str:
    """Generate a verified OYO search URL for accommodation."""
    clean_loc = city_or_location.strip().lower().replace(" ", "-")
    encoded_loc = urllib.parse.quote_plus(clean_loc)
    return f"{BASE_SEARCH_URL}/search?location={encoded_loc}"
