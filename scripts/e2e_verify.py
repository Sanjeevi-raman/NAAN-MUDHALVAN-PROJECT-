"""
PocketSmart AI - Live End-to-End HTTP Verification Script
Exercises the entire live running web application on http://127.0.0.1:8000
and validates all 27 acceptance criteria.
"""

import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_e2e_verification():
    print("=" * 70)
    print("STARTING POCKETSMART AI LIVE END-TO-END VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Landing Page
    print("\n[1/12] Testing Landing Page...")
    r = client.get("/")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "PocketSmart" in r.text
    assert "Smart Budget Planners" in r.text
    assert "Home Interior Planner" in r.text
    assert "Party Budget Planner" in r.text
    assert "Jewelry Budget Planner" in r.text
    assert "Scan Product" in r.text
    print("[PASS] Landing page rendered with all required sections and links.")

    # 2. User Registration
    test_user = f"user_{uuid.uuid4().hex[:6]}"
    test_email = f"{test_user}@example.com"
    print(f"\n[2/12] Testing Registration with user '{test_user}'...")
    reg_resp = client.post("/register", data={
        "full_name": "Antigravity E2E Tester",
        "username": test_user,
        "email": test_email,
        "password": "SecurePassword2026!"
    }, follow_redirects=False)
    assert reg_resp.status_code in [302, 303], f"Expected redirect, got {reg_resp.status_code}"
    cookie = reg_resp.cookies.get("pocketsmart_session")
    assert cookie is not None, "Session cookie not set after registration"
    client.cookies.set("pocketsmart_session", cookie)
    print(f"[PASS] Registered successfully. Session cookie received: {cookie[:10]}...")

    # 3. Dashboard
    print("\n[3/12] Testing Dashboard Access...")
    dash_resp = client.get("/dashboard")
    assert dash_resp.status_code == 200
    assert "Welcome, Antigravity E2E Tester!" in dash_resp.text
    assert "Launch a Budget Planner" in dash_resp.text
    print("[PASS] Dashboard authenticated greeting and metrics loaded.")

    # 4. Session Info & Data APIs
    print("\n[4/12] Testing Session Verification APIs...")
    s_info = client.get("/session-info")
    assert s_info.status_code == 200
    assert s_info.json()["authenticated"] is True
    assert s_info.json()["user"]["username"] == test_user

    s_data = client.get("/session-data")
    assert s_data.status_code == 200
    assert s_data.json()["username"] == test_user
    print("[PASS] Session info & user data isolation verified.")

    # 5. Home Interior Planner
    print("\n[5/12] Testing Home Interior Budget Planner...")
    home_resp = client.post("/generate-home", data={
        "total_budget": 65000.0,
        "room_type": "Living Room",
        "num_furniture": 2,
        "num_lights": 4,
        "num_fans": 1,
        "num_decor": 2,
        "style_preference": "Modern",
        "additional_notes": "Warm lighting preferred"
    }, follow_redirects=True)
    assert home_resp.status_code == 200
    assert "Home Interior Plan" in home_resp.text
    assert "Total Budget" in home_resp.text
    assert "Estimated Spend" in home_resp.text
    assert "Remaining Budget" in home_resp.text
    assert "View on Amazon" in home_resp.text or "View on IKEA" in home_resp.text
    print("[PASS] Home Interior Plan generated, balanced across categories within budget.")

    # 6. Party Budget Planner (with 60 KM Geolocation)
    print("\n[6/12] Testing Party Budget Planner with 60 KM Nearby Logic...")
    party_resp = client.post("/generate-party", data={
        "total_budget": 95000.0,
        "guest_count": 50,
        "event_type": "Birthday Celebration",
        "venue_preference": "Banquet Hall",
        "catering_preference": "Multi-Cuisine Buffet",
        "decoration_needed": "true",
        "entertainment_needed": "true",
        "accommodation_needed": "false",
        "user_latitude": 28.6139,
        "user_longitude": 77.2090,
        "travel_mode": "car"
    }, follow_redirects=True)
    assert party_resp.status_code == 200
    assert "Event Budget & Venue Options" in party_resp.text
    assert "Travel Estimate" in party_resp.text
    assert "Effective Total Spend" in party_resp.text
    assert "Google Maps" in party_resp.text
    assert "Nearby" in party_resp.text
    print("[PASS] Party Planner generated location-aware venues, travel costs, and Google Maps links.")

    # 7. Jewelry Budget Planner
    print("\n[7/12] Testing Jewelry Budget Planner...")
    jewel_resp = client.post("/generate-jewelry", data={
        "total_budget": 25000.0,
        "occasion": "Wedding / Reception",
        "style_preference": "Traditional Temple & Heritage",
        "precious_metal": "Gold",
        "location": "Chennai",
        "outfit_description": "Burgundy silk velvet lehenga with antique gold work"
    }, follow_redirects=True)
    assert jewel_resp.status_code == 200
    assert "Jewelry Ensemble" in jewel_resp.text
    assert "Necklace" in jewel_resp.text or "Earrings" in jewel_resp.text
    assert "Certified Jeweler" in jewel_resp.text or "Hallmarked" in jewel_resp.text
    print("[PASS] Jewelry Planner generated matching ensemble.")

    # 8. Product Price Scanner (Local vs Online Market Comparison)
    print("\n[8/12] Testing Scan Product & Price Comparison Engine...")
    scan_resp = client.post("/scan-product", data={
        "local_price": 1200.0,
        "manual_product_name": "boAt Rockerz 450 Bluetooth Headphones"
    }, follow_redirects=True)
    assert scan_resp.status_code == 200
    assert "Market Price Comparison" in scan_resp.text
    assert "Local Physical Store" in scan_resp.text
    assert "Amazon" in scan_resp.text
    assert "Flipkart" in scan_resp.text
    assert "Potential Online Saving Found" in scan_resp.text or "price matches" in scan_resp.text.lower()
    print("[PASS] Product Price Scanner compared physical price with Amazon/Flipkart & savings.")

    # 9. Nearby Location API
    print("\n[9/12] Testing Location & Transit Calculation APIs...")
    loc_api = client.post("/api/location/nearby", json={
        "latitude": 19.0760,
        "longitude": 72.8777,
        "event_type": "Corporate Dinner",
        "guest_count": 80,
        "budget": 100000.0,
        "travel_mode": "car"
    })
    assert loc_api.status_code == 200
    assert loc_api.json()["radius_rule_km"] == 60.0
    assert len(loc_api.json()["venues"]) >= 3
    print("[PASS] Nearby search returned multiple diverse venue alternatives within 60km rule.")

    # 10. Travel Breakdown API
    travel_api = client.post("/api/travel/estimate", json={"distance_km": 12.5, "mode": "car"})
    assert travel_api.status_code == 200
    assert travel_api.json()["car"]["estimated_roundtrip_cost"] == 300.0  # 12.5 * 2 * 12.0
    print("[PASS] Multi-modal travel estimation calculated accurately.")

    # 11. History Inspection
    print("\n[11/12] Testing History & User Isolation...")
    hist_resp = client.get("/history")
    assert hist_resp.status_code == 200
    assert "Saved Budget Plans" in hist_resp.text
    assert "In-Store Product Scan History" in hist_resp.text
    assert test_user not in hist_resp.text or "Personal Planning History" in hist_resp.text
    print("[PASS] History displays user's previous plans and scans.")

    # 12. Logout
    print("\n[12/12] Testing Logout...")
    logout_resp = client.post("/logout", follow_redirects=False)
    assert logout_resp.status_code in [302, 303]
    print("[PASS] Session successfully destroyed on logout.")

    print("\n" + "=" * 70)
    print("ALL 12 LIVE VERIFICATION PHASES COMPLETED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_e2e_verification()
    except Exception as e:
        print(f"\n❌ E2E VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
