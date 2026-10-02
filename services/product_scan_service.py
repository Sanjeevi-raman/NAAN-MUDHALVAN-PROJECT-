"""
PocketSmart AI - Product Scanning Service
Processes product images captured from camera or uploaded by user,
identifies product specifications and confidence via Gemini Multimodal AI,
queries online price observation adapters, and saves scan history.
"""

import os
import uuid
import json
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile
from PIL import Image
import io

from database.database import get_db_connection
from models.history import ProductScanResult, OnlinePriceItem
from services.gemini_service import analyze_product_image_for_scanner, is_ai_available
from services.price_comparison_service import calculate_online_observed_prices, compute_savings_and_difference

logger = logging.getLogger(__name__)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

async def process_product_scan(
    image_file: Optional[UploadFile],
    local_price: float,
    manual_product_name: Optional[str] = None,
    user_id: Optional[int] = None
) -> ProductScanResult:
    """
    Scan product image, run Gemini multimodal analysis, compare prices,
    and persist results.
    """
    image_rel_path = None
    ai_result = None
    brand = None
    product_name = manual_product_name or "Scanned Store Item"
    model = None
    variant = None
    category = "General Retail"
    color = None
    visible_specs = []
    match_confidence = "Unable to Identify"
    notes = ""
    is_live = False

    # 1. Process uploaded/captured image if provided
    if image_file and image_file.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename_ext = os.path.splitext(image_file.filename)[1].lower()
        if not filename_ext or filename_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            filename_ext = ".jpg"
        
        unique_filename = f"scan_{uuid.uuid4().hex[:12]}{filename_ext}"
        saved_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        file_bytes = await image_file.read()
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
        image_rel_path = f"/uploads/{unique_filename}"

        # 2. Invoke Gemini Multimodal AI if available
        if is_ai_available():
            try:
                mime_type = image_file.content_type or "image/jpeg"
                ai_data = await analyze_product_image_for_scanner(file_bytes, mime_type, local_price)
                if ai_data:
                    ai_result = ai_data
                    brand = ai_data.get("brand")
                    if ai_data.get("product_name"):
                        product_name = ai_data.get("product_name")
                    model = ai_data.get("model")
                    variant = ai_data.get("variant")
                    category = ai_data.get("category", "Retail")
                    color = ai_data.get("color")
                    match_confidence = ai_data.get("match_confidence", "Likely Match")
                    visible_specs = ai_data.get("visible_specs", [])
                    notes = ai_data.get("identification_notes", "")
                    is_live = True
            except Exception as e:
                logger.error(f"Multimodal scan processing error: {e}")
                notes = f"AI analysis encountered an error. Proceeding with fallback detection."

    # 3. Fallback heuristic identification if AI could not identify or was offline
    if not ai_result:
        if manual_product_name and len(manual_product_name.strip()) > 2:
            match_confidence = "Likely Match"
            notes = "Identified using verified user input specifications."
        else:
            match_confidence = "Possible Match"
            notes = "Identified general store merchandise. Enter exact model for tighter match."

    # 4. Compare observed online prices
    online_prices = calculate_online_observed_prices(
        product_name=product_name,
        brand=brand,
        model=model,
        local_price=local_price,
        is_live=is_live
    )

    savings_data = compute_savings_and_difference(local_price, online_prices)

    scan_result = ProductScanResult(
        product_name=product_name,
        brand=brand,
        model=model,
        variant=variant,
        category=category,
        color=color,
        match_confidence=match_confidence,
        visible_specs=visible_specs,
        local_price=local_price,
        online_prices=online_prices,
        lowest_observed_price=savings_data["lowest_observed_price"],
        lowest_platform=savings_data["lowest_platform"],
        price_difference=savings_data["price_difference"],
        possible_saving=savings_data["possible_saving"],
        image_url=image_rel_path,
        notes=notes,
        is_demo=not is_live
    )

    # 5. Persist to DB if user is authenticated
    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO product_scans (
                    user_id, product_name, brand, model, variant, match_confidence,
                    category, local_price, lowest_online_price, price_difference,
                    possible_saving, online_prices_json, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                scan_result.product_name,
                scan_result.brand,
                scan_result.model,
                scan_result.variant,
                scan_result.match_confidence,
                scan_result.category,
                scan_result.local_price,
                scan_result.lowest_observed_price,
                scan_result.price_difference,
                scan_result.possible_saving,
                json.dumps([p.model_dump() for p in scan_result.online_prices]),
                image_rel_path
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving product scan to database: {e}")

    return scan_result
