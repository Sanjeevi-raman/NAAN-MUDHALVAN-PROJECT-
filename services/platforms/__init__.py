"""
PocketSmart AI - Platform Adapters Package
Provides search URL generation, pricing adapters, and platform metadata
for Amazon, Flipkart, IKEA, Swiggy, Zomato, and OYO.
"""

from .amazon import get_amazon_search_url, get_amazon_product_recommendations
from .flipkart import get_flipkart_search_url, get_flipkart_product_recommendations
from .ikea import get_ikea_search_url, get_ikea_product_recommendations
from .swiggy import get_swiggy_search_url
from .zomato import get_zomato_search_url
from .oyo import get_oyo_search_url
from .jeweler_shops import (
    JEWELER_BRANDS,
    REAL_JEWELRY_CATALOG,
    get_jeweler_search_url,
    get_nearby_jeweler_shops
)

__all__ = [
    "get_amazon_search_url",
    "get_amazon_product_recommendations",
    "get_flipkart_search_url",
    "get_flipkart_product_recommendations",
    "get_ikea_search_url",
    "get_ikea_product_recommendations",
    "get_swiggy_search_url",
    "get_zomato_search_url",
    "get_oyo_search_url",
    "JEWELER_BRANDS",
    "REAL_JEWELRY_CATALOG",
    "get_jeweler_search_url",
    "get_nearby_jeweler_shops"
]
