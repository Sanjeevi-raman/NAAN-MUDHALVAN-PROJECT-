"""
PocketSmart AI - Comprehensive Automated Test Suite
Tests authentication, sessions, budget planners (Home, Party, Jewelry),
60 KM location logic, travel estimations, product price scanning,
history isolation, and recommendation details.
"""

import os
import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import init_db, get_db_connection
from services.auth_service import create_session
from services.platforms.jeweler_shops import JEWELER_BRANDS

client = TestClient(app)


def verified_cookie(username):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.execute("UPDATE users SET email_verified = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return create_session(row["id"])

@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is clean and initialized for tests."""
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

# =====================================================================
# 1. AUTHENTICATION & SESSION TESTS
# =====================================================================

def test_landing_page():
    """Verify landing page loads with PocketSmart AI branding and planner links."""
    response = client.get("/")
    assert response.status_code == 200
    assert "PocketSmart" in response.text
    assert "Home Interior Planner" in response.text
    assert "Party Budget Planner" in response.text
    assert "Jewelry Budget Planner" in response.text
    assert "Scan Product" in response.text

def test_register_and_login_flow():
    """Test user registration, duplicate detection, login, and session cookie."""
    # 1. Register new user
    reg_data = {
        "full_name": "Test User",
        "username": "testuser_unique",
        "email": "testuser_unique@example.com",
        "password": "securepassword123"
    }
    reg_response = client.post("/register", data=reg_data, follow_redirects=False)
    # Registration must require email verification before activation.
    assert reg_response.status_code == 303
    assert reg_response.headers["location"].startswith("/verify-email")
    assert "pocketsmart_session" not in reg_response.cookies
    cookie = verified_cookie("testuser_unique")

    # 2. Duplicate registration should be rejected
    dup_response = client.post("/register", data=reg_data, follow_redirects=False)
    assert dup_response.status_code == 400
    assert "already registered" in dup_response.text

    # 3. Invalid login should fail
    bad_login = client.post("/login", data={"username": "testuser_unique", "password": "wrongpassword"})
    assert bad_login.status_code == 400
    assert "Invalid email or password" in bad_login.text

    # 4. Valid login sets cookie
    good_login = client.post("/login", data={"username": "testuser_unique", "password": "securepassword123"}, follow_redirects=False)
    assert good_login.status_code == 303
    cookie = good_login.cookies.get("pocketsmart_session")
    assert cookie is not None

    # 5. Access dashboard with session cookie
    dash_response = client.get("/dashboard", cookies={"pocketsmart_session": cookie})
    assert dash_response.status_code == 200
    assert "Welcome, Test User!" in dash_response.text

    # 6. Session info API returns authenticated profile
    session_resp = client.get("/session-info", cookies={"pocketsmart_session": cookie})
    assert session_resp.status_code == 200
    data = session_resp.json()
    assert data["authenticated"] is True
    assert data["user"]["username"] == "testuser_unique"

    # 7. Logout clears session
    logout_resp = client.post("/logout", cookies={"pocketsmart_session": cookie}, follow_redirects=False)
    assert logout_resp.status_code == 303

# =====================================================================
# 2. HOME INTERIOR PLANNER TESTS
# =====================================================================

def test_home_planner_budget_allocation():
    """Verify Home Planner allocates categories and does not exceed budget."""
    # Register/login user
    reg = client.post("/register", data={
        "full_name": "Home Planner User",
        "username": "home_user_99",
        "email": "home_user_99@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = verified_cookie("home_user_99")

    # Generate plan with 50,000 budget
    plan_data = {
        "total_budget": 50000.0,
        "room_type": "Living Room",
        "num_furniture": 2,
        "num_lights": 4,
        "num_fans": 1,
        "num_decor": 2,
        "style_preference": "Modern",
        "additional_notes": "Warm lighting"
    }
    resp = client.post("/generate-home", data=plan_data, cookies={"pocketsmart_session": cookie}, headers={"accept": "application/json"})
    assert resp.status_code == 200
    res_json = resp.json()
    assert "summary" in res_json
    summary = res_json["summary"]

    assert summary["planner_type"] == "home"
    assert summary["total_budget"] == 50000.0
    assert summary["total_spend"] > 0
    assert summary["remaining_budget"] >= 0
    assert len(summary["items"]) > 0

    # Ensure items have valid actionable links (no '#')
    for item in summary["items"]:
        assert item["url"].startswith("http")
        assert "#" not in item["url"]
        assert item["price"] > 0
        assert item["total_price"] > 0

# =====================================================================
# 3. PARTY BUDGET PLANNER & 60 KM NEARBY TESTS
# =====================================================================

def test_party_planner_with_geolocation_and_60km_rule():
    """Test Party Planner location awareness, 60km rule, and travel cost additions."""
    reg = client.post("/register", data={
        "full_name": "Party User",
        "username": "party_user_99",
        "email": "party_user_99@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = verified_cookie("party_user_99")

    party_data = {
        "total_budget": 80000.0,
        "guest_count": 60,
        "event_type": "Birthday Celebration",
        "venue_preference": "Banquet Hall",
        "catering_preference": "Multi-Cuisine Buffet",
        "decoration_needed": True,
        "entertainment_needed": True,
        "accommodation_needed": False,
        "user_latitude": 28.6139,  # New Delhi reference
        "user_longitude": 77.2090,
        "travel_mode": "car"
    }
    resp = client.post("/generate-party", data=party_data, cookies={"pocketsmart_session": cookie}, headers={"accept": "application/json"})
    assert resp.status_code == 200
    res_json = resp.json()
    summary = res_json["summary"]

    assert summary["planner_type"] == "party"
    assert summary["total_budget"] == 80000.0
    assert summary["total_travel_estimate"] > 0
    assert summary["effective_total"] > summary["total_spend"]  # Effective total includes travel

    # Check that nearby items within 60km have valid distance and Google Maps links
    venues = [i for i in summary["items"] if "Venue" in i["category"]]
    assert len(venues) >= 2  # Multiple venue alternatives
    for v in venues:
        assert v["google_maps_url"].startswith("https://www.google.com/maps/")
        assert v["distance_km"] is not None
        assert v["travel_time_minutes"] is not None
        assert v["travel_cost_estimate"] is not None
        if v["distance_km"] <= 60.0:
            assert v["is_nearby"] is True

# =====================================================================
# 4. JEWELRY PLANNER (TEXT & MULTIMODAL) TESTS
# =====================================================================

def test_jewelry_planner_text_only():
    """Test Jewelry planner generates styled piece recommendations with budget constraint."""
    reg = client.post("/register", data={
        "full_name": "Jewelry User",
        "username": "jewelry_user_99",
        "email": "jewelry_user_99@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = verified_cookie("jewelry_user_99")

    jewel_data = {
        "total_budget": 20000.0,
        "occasion": "Wedding / Reception",
        "style_preference": "Traditional Temple & Heritage",
        "precious_metal": "Gold",
        "location": "Chennai",
        "outfit_description": "Red Kanjeevaram silk saree with pure gold zari"
    }
    resp = client.post("/generate-jewelry", data=jewel_data, cookies={"pocketsmart_session": cookie}, headers={"accept": "application/json"})
    assert resp.status_code == 200
    res_json = resp.json()
    summary = res_json["summary"]

    assert summary["planner_type"] == "jewelry"
    assert summary["total_budget"] == 20000.0
    assert len(summary["items"]) >= 2
    for item in summary["items"]:
        assert item["url"].startswith("http")
        assert item["platform"] in ["Tanishq", "CaratLane", "BlueStone", "Malabar Gold & Diamonds", "Kalyan Jewellers", "GIVA", "Amazon", "Flipkart"]
        assert "bangle" not in item["category"].lower()
        assert "bangle" not in item["name"].lower()
    
    # Verify presence of certified nearby jeweler shops
    assert summary.get("nearby_shops") is not None
    assert len(summary["nearby_shops"]) >= 3

def test_jewellery_platform_links_are_approved():
    """Ensure jewellery destinations stay within the supplied official links."""
    expected_links = {
        "Amazon India": "https://www.amazon.in/?utm_source=chatgpt.com",
        "Flipkart": "https://www.flipkart.com/?utm_source=chatgpt.com",
        "Myntra": "https://www.myntra.com/?utm_source=chatgpt.com",
        "Tata CLiQ": "https://www.tatacliq.com/?utm_source=chatgpt.com",
        "Tanishq": "https://www.tanishq.co.in/?utm_source=chatgpt.com",
        "GRT Jewellers": "https://www.grtjewels.com/?utm_source=chatgpt.com",
        "Joyalukkas": "https://www.joyalukkas.in/?utm_source=chatgpt.com",
        "Malabar Gold & Diamonds": "https://www.malabargoldanddiamonds.com/?utm_source=chatgpt.com",
        "Kalyan Jewellers": "https://www.kalyanjewellers.net/?utm_source=chatgpt.com",
        "CaratLane": "https://www.caratlane.com/?utm_source=chatgpt.com",
        "BlueStone": "https://www.bluestone.com/?utm_source=chatgpt.com",
        "GIVA": "https://www.giva.co/?utm_source=chatgpt.com",
        "Candere": "https://www.candere.com/?utm_source=chatgpt.com",
        "Mia by Tanishq": "https://www.miabytanishq.com/?utm_source=chatgpt.com",
        "Melorra": "https://www.melorra.com/?utm_source=chatgpt.com",
    }
    assert {brand: info["official_site"] for brand, info in JEWELER_BRANDS.items()} == expected_links

# =====================================================================
# 5. PRODUCT PRICE SCANNER TESTS
# =====================================================================

def test_product_price_scanner_comparison_and_savings():
    """Verify local retail price vs online observed prices comparison and savings logic."""
    reg = client.post("/register", data={
        "full_name": "Scanner User",
        "username": "scanner_user_99",
        "email": "scanner_user_99@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie = verified_cookie("scanner_user_99")

    # Local price ₹1000
    scan_data = {
        "local_price": 1000.0,
        "manual_product_name": "boAt Rockerz 450 Bluetooth On Ear Headphones"
    }
    resp = client.post("/scan-product", data=scan_data, cookies={"pocketsmart_session": cookie}, headers={"accept": "application/json"})
    assert resp.status_code == 200
    result = resp.json()

    assert result["local_price"] == 1000.0
    assert "boAt Rockerz" in result["product_name"]
    assert len(result["online_prices"]) >= 2  # Amazon and Flipkart

    # Verify shipping and payable calculations
    for p in result["online_prices"]:
        assert p["total_payable"] == p["price"] + p["shipping"]
        assert p["url"].startswith("http")

    assert result["lowest_observed_price"] is not None
    assert result["price_difference"] == round(1000.0 - result["lowest_observed_price"], 2)
    assert result["possible_saving"] >= 0

# =====================================================================
# 6. USER DATA ISOLATION & HISTORY TESTS
# =====================================================================

def test_user_history_isolation():
    """Verify that users only see their own plans and cannot access other users' data."""
    # User A
    user_a = client.post("/register", data={
        "full_name": "User Alpha",
        "username": "user_alpha",
        "email": "alpha@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie_a = verified_cookie("user_alpha")

    # User B
    user_b = client.post("/register", data={
        "full_name": "User Beta",
        "username": "user_beta",
        "email": "beta@example.com",
        "password": "password123"
    }, follow_redirects=False)
    cookie_b = verified_cookie("user_beta")

    # User A generates a plan
    client.post("/generate-home", data={
        "total_budget": 45000.0,
        "room_type": "Bedroom",
        "num_furniture": 1,
        "num_lights": 2,
        "num_fans": 1,
        "num_decor": 1,
        "style_preference": "Modern"
    }, cookies={"pocketsmart_session": cookie_a}, headers={"accept": "application/json"})

    # User A history has 1 plan
    resp_a = client.get("/api/history", cookies={"pocketsmart_session": cookie_a})
    assert len(resp_a.json()) == 1

    # User B history has 0 plans (isolated!)
    resp_b = client.get("/api/history", cookies={"pocketsmart_session": cookie_b})
    assert len(resp_b.json()) == 0

# =====================================================================
# 7. LOCATION & TRAVEL API TESTS
# =====================================================================

def test_travel_estimate_api():
    """Test transit cost calculations across car, bike, and public transport."""
    resp = client.post("/api/travel/estimate", json={"distance_km": 15.0, "mode": "car"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["distance_km"] == 15.0
    assert data["car"]["estimated_roundtrip_cost"] > 0
    assert data["bike"]["estimated_roundtrip_cost"] > 0
    assert data["public_transit"]["estimated_roundtrip_cost"] > 0
    assert data["car"]["estimated_roundtrip_cost"] > data["bike"]["estimated_roundtrip_cost"]

def test_nearby_venues_api():
    """Test nearby venue search API with 60km rule ranking."""
    resp = client.post("/api/location/nearby", json={
        "latitude": 19.0760,  # Mumbai reference
        "longitude": 72.8777,
        "event_type": "Wedding",
        "guest_count": 100,
        "budget": 120000.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["radius_rule_km"] == 60.0
    assert len(data["venues"]) > 0
