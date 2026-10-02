"""
PocketSmart AI - Gemini AI Service
Interfaces with Google Gemini for intelligent text and multimodal recommendations,
product scanning, and budget optimization.
Supports configurable models, structured JSON responses, and resilient fallbacks.
"""

import os
import json
import logging
import io
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

logger = logging.getLogger(__name__)

# Configurable environment settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

# Fallback models in order of priority if primary is unavailable
FALLBACK_MODELS = list(dict.fromkeys([DEFAULT_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]))

def get_gemini_client():
    """Initialize and return the official Google GenAI client if API key is present."""
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize google-genai client: {e}")
        return None

def is_ai_available() -> bool:
    """Check if Gemini API key is configured."""
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)

def extract_json_from_text(text: str) -> Optional[Any]:
    """Extract and parse JSON from a model response string, stripping code blocks."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to locate first '{' or '[' and last '}' or ']'
        start_idx = min(
            (pos for pos in [cleaned.find('{'), cleaned.find('[')] if pos != -1),
            default=-1
        )
        end_idx = max(
            (pos for pos in [cleaned.rfind('}'), cleaned.rfind(']')] if pos != -1),
            default=-1
        )
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(cleaned[start_idx:end_idx + 1])
            except Exception:
                pass
        return None

import asyncio

async def generate_ai_text_recommendations(prompt: str, system_instruction: str = "") -> Optional[Dict[str, Any]]:
    """Generate structured JSON recommendations using Gemini with model fallback and strict timeout."""
    client = get_gemini_client()
    if not client:
        return None

    full_prompt = f"{system_instruction}\n\n{prompt}\n\nIMPORTANT: Return ONLY valid, parseable JSON matching the requested schema. Do not include markdown code block formatting if possible."

    for model_name in FALLBACK_MODELS:
        try:
            # Run in thread with 5 second timeout to avoid blocking event loop
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=model_name,
                    contents=full_prompt
                ),
                timeout=5.0
            )
            if response and response.text:
                parsed = extract_json_from_text(response.text)
                if parsed:
                    return parsed
        except asyncio.TimeoutError:
            logger.warning(f"Gemini call to model {model_name} timed out after 5s. Proceeding to fallback.")
            break  # If network to Google is hanging, quickly fallback to instant domain engine
        except Exception as e:
            logger.warning(f"Gemini call to model {model_name} failed: {e}")
            continue

    return None

async def analyze_outfit_image_for_jewelry(
    image_bytes: bytes,
    mime_type: str,
    budget: float,
    occasion: str,
    style_preference: str,
    precious_metal: str = "Gold"
) -> Optional[Dict[str, Any]]:
    """
    Multimodal Gemini analysis of outfit image for 100% authentic precious jewelry matching.
    Only recommends real precious pieces (Gold, Silver, Platinum, Diamond) from certified jewelers.
    STRICTLY NO imitation/costume jewelry and NO bangles.
    """
    client = get_gemini_client()
    if not client:
        return None

    system_instruction = (
        "You are an expert precious jewelry consultant and certified gemologist for PocketSmart AI. "
        "Recommend ONLY 100% authentic fine jewelry: Hallmarked Gold (22K/18K BIS), Certified 925 Sterling Silver, "
        "Pure Platinum (Pt 950), or Certified Diamonds (IGI/SGL). "
        "DO NOT recommend bangles or artificial/imitation jewelry. Focus strictly on Necklaces/Pendants, Earrings/Studs, and Rings."
    )
    prompt = f"""
Analyze this outfit image for a {occasion} event.
The user has a total real jewelry budget of INR ₹{budget:,.2f}, prefers '{style_preference}', and requested material: '{precious_metal}'.

CRITICAL RULES:
1. MATERIAL MUST BE EXCLUSIVELY: Gold, Silver, Platinum, or Diamond (these 4 only).
2. REAL JEWEL PIECES ONLY: Necklace / Pendant / Chain, Earrings / Studs, and Finger Ring / Solitaire.
3. ABSOLUTELY NO BANGLES and NO imitation/costume jewelry.
4. Recommend pieces available from certified jeweler houses: Tanishq, CaratLane, BlueStone, Malabar Gold & Diamonds, Kalyan Jewellers, or GIVA (for 925 silver).

Provide a structured JSON output with this schema:
{{
  "outfit_analysis": {{
    "dominant_colors": ["color1", "color2"],
    "neckline_or_cut": "V-neck / Boat / High neck / Sweetheart / Round",
    "formality_level": "Festive / Wedding / Evening Party / Elegant Casual",
    "recommended_metal": "Gold (22K/18K) / 925 Silver / Pt 950 Platinum / Diamond",
    "styling_advice": "Detailed styling advice tailored to the neckline and fabric"
  }},
  "recommendations": [
    {{
      "name": "Full Authentic Product Name (e.g. Tanishq 22K Gold Pendant or CaratLane Diamond Studs)",
      "category": "Necklace / Pendant" / "Earrings / Studs" / "Ring / Solitaire",
      "material": "Gold" / "Silver" / "Platinum" / "Diamond",
      "purity_certification": "BIS 916 Hallmarked / Pt 950 / 925 Sterling / IGI Diamond",
      "brand": "Tanishq / CaratLane / BlueStone / Malabar Gold / Kalyan / GIVA",
      "description": "Specific craftsmanship, metal caratage, and stone cut details",
      "price": 15000.0,
      "quantity": 1,
      "total_price": 15000.0,
      "search_query": "Exact search query for this fine piece",
      "reason": "Why this precious piece complements the outfit cut and skin tone"
    }}
  ]
}}
"""
    try:
        from google.genai import types
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        
        for model_name in FALLBACK_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[part, prompt]
                )
                if response and response.text:
                    parsed = extract_json_from_text(response.text)
                    if parsed:
                        return parsed
            except Exception as e:
                logger.warning(f"Multimodal jewelry analysis failed on {model_name}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error preparing multimodal payload: {e}")

    return None

async def analyze_product_image_for_scanner(
    image_bytes: bytes,
    mime_type: str,
    local_price: float
) -> Optional[Dict[str, Any]]:
    """
    Multimodal Gemini analysis for Scan Product feature.
    Identifies brand, model, variant, specifications, and match confidence.
    """
    client = get_gemini_client()
    if not client:
        return None

    prompt = f"""
You are a retail product scanner AI for PocketSmart AI.
The user is in a physical store where this product is priced at INR ₹{local_price:,.2f}.
Inspect the product image carefully:
1. Identify brand, exact product name, model number, variant, size/capacity, and visible colors/specs.
2. Read any visible barcodes, labels, or text on the package.
3. Determine Match Confidence: "Exact Match" (if model/text clearly readable), "Likely Match" (if recognizable model), "Possible Match" (generic shape/category visible), or "Unable to Identify" (blurry/unclear).
4. Do NOT invent or hallucinate unreadable model numbers. If unclear, specify what is missing.

Return ONLY this JSON format:
{{
  "brand": "Brand name or null",
  "product_name": "Full recognized product name",
  "model": "Model number or null",
  "variant": "Variant / size / capacity or null",
  "color": "Color or null",
  "category": "Electronics / Home Appliances / Groceries / Fashion / Personal Care",
  "match_confidence": "Exact Match" / "Likely Match" / "Possible Match" / "Unable to Identify",
  "visible_specs": ["spec 1", "spec 2"],
  "search_terms": {{
    "amazon_query": "Optimized search query for Amazon",
    "flipkart_query": "Optimized search query for Flipkart"
  }},
  "identification_notes": "Brief notes on how it was identified"
}}
"""
    try:
        from google.genai import types
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        for model_name in FALLBACK_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[part, prompt]
                )
                if response and response.text:
                    parsed = extract_json_from_text(response.text)
                    if parsed:
                        return parsed
            except Exception as e:
                logger.warning(f"Product scanner image analysis failed on {model_name}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error in analyze_product_image_for_scanner: {e}")

    return None
