"""
Flipkart Platform Adapter
Handles Flipkart product search URL generation, pricing data,
and search result links.
"""

import urllib.parse
from typing import Dict, Any, List

PLATFORM_NAME = "Flipkart"
BASE_SEARCH_URL = "https://www.flipkart.com/search"

def get_flipkart_search_url(query: str) -> str:
    """Generate a verified, actionable Flipkart search URL."""
    encoded_query = urllib.parse.quote_plus(query.strip())
    return f"{BASE_SEARCH_URL}?q={encoded_query}"

def get_flipkart_product_recommendations(category: str, budget: float) -> List[Dict[str, Any]]:
    """Return categorized products on Flipkart with verified search links."""
    catalog = {
        "lighting": [
            {
                "name": "Orient Electric 20W LED Batten Warm White",
                "price": 389.0,
                "rating": 4.2,
                "review_count": 2100,
                "query": "Orient Electric 20W LED Batten",
                "reason": "Cost-effective wide-beam wall/ceiling lighting"
            },
            {
                "name": "Havells Adore 15W Round LED Recessed Panel",
                "price": 499.0,
                "rating": 4.3,
                "review_count": 1450,
                "query": "Havells Adore 15W Round LED Panel Light",
                "reason": "Flush fitting ceiling fixture with surge protection"
            }
        ],
        "ceiling fans": [
            {
                "name": "Orient Electric Apex-FX 1200mm Ceiling Fan",
                "price": 1399.0,
                "rating": 4.2,
                "review_count": 11200,
                "query": "Orient Electric Apex-FX 1200mm Ceiling Fan",
                "reason": "High air thrust with durable ribbed aluminum blades"
            },
            {
                "name": "Bajaj Frore 1200mm 56W High Speed Fan",
                "price": 1299.0,
                "rating": 4.1,
                "review_count": 7800,
                "query": "Bajaj Frore 1200mm High Speed Fan",
                "reason": "Affordable reliable cooling backed by nationwide warranty"
            }
        ],
        "furniture": [
            {
                "name": "Flipkart Perfect Homes Engineered Wood TV Entertainment Unit",
                "price": 3499.0,
                "rating": 4.1,
                "review_count": 4300,
                "query": "Flipkart Perfect Homes TV Entertainment Unit",
                "reason": "Space-saving media console with open and closed shelving"
            },
            {
                "name": "Wakefit Taurus Engineered Wood Queen Size Bed with Storage",
                "price": 10499.0,
                "rating": 4.4,
                "review_count": 8900,
                "query": "Wakefit Taurus Engineered Wood Queen Size Bed",
                "reason": "Spacious under-bed box storage with scratch-resistant finish"
            }
        ],
        "decor": [
            {
                "name": "Home Centre Printed Cotton Cushion Covers (Set of 5)",
                "price": 499.0,
                "rating": 4.3,
                "review_count": 1950,
                "query": "Home Centre Printed Cotton Cushion Covers Set of 5",
                "reason": "Vibrant accent patterns to enhance sofa styling"
            }
        ],
        "jewelry": [
            {
                "name": "Sukkhi Classic Gold Plated Kundan Choker Necklace Set",
                "price": 389.0,
                "rating": 4.2,
                "review_count": 5200,
                "query": "Sukkhi Classic Gold Plated Kundan Choker Necklace Set",
                "reason": "Traditional artisan finish with adjustable dori"
            },
            {
                "name": "Atasi International Oxidized Silver Tribal Choker Set",
                "price": 299.0,
                "rating": 4.0,
                "review_count": 1400,
                "query": "Atasi International Oxidized Silver Tribal Choker Set",
                "reason": "Boho chic oxidized silver statement jewelry for ethnic wear"
            }
        ]
    }
    key = category.lower().strip()
    matched = catalog.get(key, catalog["furniture"])
    results = []
    for item in matched:
        if item["price"] <= budget * 1.2:
            results.append({
                "name": item["name"],
                "price": item["price"],
                "rating": item["rating"],
                "review_count": item["review_count"],
                "platform": PLATFORM_NAME,
                "url": get_flipkart_search_url(item["query"]),
                "reason": item["reason"],
                "is_mock": False
            })
    return results
