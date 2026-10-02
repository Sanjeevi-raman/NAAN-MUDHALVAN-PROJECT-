"""
PocketSmart AI - Extended Validation Tests
Tests edge cases: negative budgets, high budgets, missing website handling,
scan history API, session endpoints, and recommendation detail pages.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import init_db, get_db_connection

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_clean_db():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions;")
    cursor.execute("DELETE FROM recommendation_results;")
    cursor.execute("DELETE FROM recommendation_histories;")
    cursor.execute("DELETE FROM planner_requests;")
    cursor.execute("DELETE FROM product_scans;")
    cursor.execute("DELETE FROM users;")
    conn.commit()
    conn.close()

def test_invalid_input_validation():
    """Verify system blocks non-positive budgets and invalid values."""
    reg = client.post("/register", data={
        "full_name": "Val User",
        "username": "val_user",
        "email": "val@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = reg.cookies.get("pocketsmart_session")

    # Negative budget in Home Planner
    resp1 = client.post("/generate-home", data={
        "total_budget": -500.0,
        "room_type": "Kitchen",
        "num_furniture": 1
    }, cookies={"pocketsmart_session": cookie})
    assert resp1.status_code == 400
    assert "greater than zero" in resp1.text

    # Zero guest count in Party Planner
    resp2 = client.post("/generate-party", data={
        "total_budget": 50000.0,
        "guest_count": 0,
        "event_type": "Birthday"
    }, cookies={"pocketsmart_session": cookie})
    assert resp2.status_code == 400
    assert "at least 1" in resp2.text

    # Negative price in Product Scanner
    resp3 = client.post("/scan-product", data={
        "local_price": -20.0
    }, cookies={"pocketsmart_session": cookie})
    assert resp3.status_code == 400
    assert "greater than zero" in resp3.text

def test_missing_website_graceful_handling():
    """Verify that venues without an official website do not show dead links."""
    reg = client.post("/register", data={
        "full_name": "Venue User",
        "username": "venue_user",
        "email": "venue@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = reg.cookies.get("pocketsmart_session")

    resp = client.post("/generate-party", data={
        "total_budget": 60000.0,
        "guest_count": 40,
        "event_type": "Anniversary Party",
        "user_latitude": 12.9716,  # Bengaluru reference
        "user_longitude": 77.5946,
        "travel_mode": "car"
    }, cookies={"pocketsmart_session": cookie})
    assert resp.status_code == 200
    # Emerald Greens has website=None, verify 'Website Unavailable' is displayed
    assert "Website Unavailable" in resp.text
    # And Google Maps link IS present and working
    assert "maps/search" in resp.text

def test_scan_history_api():
    """Verify logged-in user scans are stored and retrieved from /api/scan-history."""
    reg = client.post("/register", data={
        "full_name": "Scanner Logger",
        "username": "scanner_logger",
        "email": "scanlog@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = reg.cookies.get("pocketsmart_session")

    # Perform 2 scans
    client.post("/scan-product", data={
        "local_price": 2499.0,
        "manual_product_name": "Logitech MX Master 3S Mouse"
    }, cookies={"pocketsmart_session": cookie})

    client.post("/scan-product", data={
        "local_price": 450.0,
        "manual_product_name": "Syska Smart LED Bulb 9W"
    }, cookies={"pocketsmart_session": cookie})

    # Retrieve history API
    history_resp = client.get("/api/scan-history", cookies={"pocketsmart_session": cookie})
    assert history_resp.status_code == 200
    scans = history_resp.json()
    assert len(scans) == 2
    assert "Logitech" in scans[0]["product_name"] or "Logitech" in scans[1]["product_name"]
    assert "Syska" in scans[0]["product_name"] or "Syska" in scans[1]["product_name"]

def test_recommendation_details_page():
    """Verify recommendation inspection page for both a whole plan and individual item."""
    reg = client.post("/register", data={
        "full_name": "Detail Checker",
        "username": "detail_checker",
        "email": "detail@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = reg.cookies.get("pocketsmart_session")

    # Generate home plan
    plan_resp = client.post("/generate-home", data={
        "total_budget": 70000.0,
        "room_type": "Dining Room",
        "num_furniture": 2,
        "num_lights": 3,
        "num_fans": 1,
        "num_decor": 2,
        "style_preference": "Scandinavian"
    }, cookies={"pocketsmart_session": cookie}, headers={"accept": "application/json"})

    history_id = plan_resp.json()["history_id"]
    assert history_id is not None

    # Inspect the saved plan by history_id
    detail_resp = client.get(f"/recommendations-details?history_id={history_id}", cookies={"pocketsmart_session": cookie})
    assert detail_resp.status_code == 200
    assert "Dining Room" in detail_resp.text or "Home" in detail_resp.text
    assert "Itemized Recommendations" in detail_resp.text
