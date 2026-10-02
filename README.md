# PocketSmart AI — Your Smart Budget & Recommendation Assistant

PocketSmart AI is a production-quality full-stack web application designed for smart, budget-aware lifestyle planning and in-store retail price comparison. Built with **FastAPI**, **SQLite**, **Jinja2**, and **Google Gemini AI**, PocketSmart AI optimizes user expenditures across home renovation, social events, jewelry styling, and physical store purchases.

---

## 🌟 Core Features

### 1. Home Interior Budget Planner (`/home-planner`)
- Room-by-room planning (**Living Room**, **Kitchen**, **Bedroom**, **Dining Room**, **Home Office**).
- Balanced category distribution across **Furniture** (50%), **Lighting** (20%), **Ceiling Fans** (15%), and **Decor** (15%).
- Configurable item counts (number of furniture pieces, LED panel lights, BLDC ceiling fans, wall decor).
- Generates actionable, verified search & product URLs on **Amazon India**, **Flipkart**, and **IKEA India**.
- Visual budget summary panel featuring spend allocation, progress meters, and remaining balance indicators.

### 2. Party Budget Planner & 60 KM Nearby Location Rule (`/party-planner`)
- Handles **Birthday**, **Wedding**, **Corporate Event**, **Anniversary**, and **Social Gathering** budgeting.
- **60 KM Nearby Rule**: Uses device/browser geolocation (`navigator.geolocation`) to identify event venues within a 60-kilometer radius.
- **Transparent Transit Costing**: Calculates one-way travel durations and round-trip travel expenses for **Car** (₹12/km), **Two-Wheeler/Bike** (₹4.5/km), and **Public Transit** (₹2/km).
- **Effective Total Cost**: Automatically computes `Venue/Service Cost + Estimated Travel Expense = Total Effective Spend`.
- **Diverse Venue Alternatives**: Never defaults only to OYO. Suggests air-conditioned banquet halls, open lawns, rooftop lounges, and community spaces.
- **Actionable Links**: Direct **Google Maps** search & directions links, and verified official websites (with graceful "Website Unavailable" fallback badges).
- Food catering integration with **Swiggy** and **Zomato** search adapters.

### 3. Jewelry Budget Planner (`/jewelry-planner`)
- Multimodal outfit-coordinated jewelry recommendations.
- **Dual Input Modes**: Supports **Text-Only** and **Text + Image** (outfit photo upload or camera capture).
- **Gemini Multimodal Vision AI**: Analyzes uploaded clothing photos for dominant colors, neckline geometry, fabric formality, and recommends matching metal tones (Gold, Sterling Silver, Kundan, Oxidized).
- Occasion-based budget split covering statement necklaces, matching earrings, and bangles.

### 4. Scan Product & In-Store Price Comparison (`/scan-product`)
- **Camera & Image Upload**: Allows consumers to snap photos of retail items directly in physical stores using their device camera (`getUserMedia` with rear-facing camera preference) or upload from the gallery.
- **Gemini Multimodal Product Recognition**: Identifies brand, product name, model number, variant, specifications, and assigns a match confidence (**Exact Match**, **Likely Match**, **Possible Match**, **Unable to Identify**).
- **Physical vs. Online Price Comparison**: User inputs the local shop quoted price (e.g., ₹1,000). PocketSmart AI checks observed online prices on **Amazon** and **Flipkart**.
- **Total Payable Cost Analysis**: Factors in shipping and delivery fees so users never get misled by shipping surcharges.
- **Possible Savings Highlight**: Calculates the price difference and displays potential savings with one-click links to buy online.

### 5. Authentication, Sessions & History (`/login`, `/register`, `/history`, `/dashboard`)
- Secure password hashing using cryptographic **PBKDF2-HMAC-SHA256** with unique salts.
- Session cookie and Bearer token support.
- User data isolation: users only see their own recommendation plans and product price scan histories.
- Ability to inspect saved plans and itemized breakdowns at `/recommendations-details`.

---

## 🏗️ Architecture & Technology Stack

```
USER (Desktop / Mobile Browser)
  │
  ├── Browser Geolocation API (HTML5 navigator.geolocation)
  ├── HTML5 Camera Stream (navigator.mediaDevices.getUserMedia)
  │
  ▼
FASTAPI BACKEND (Python 3.12 / Uvicorn)
  │
  ├── Security & Sessions (PBKDF2-HMAC-SHA256, HTTP-only Cookie / Bearer)
  ├── SQLite Database Layer (database/database.py)
  │
  ├── Recommendation Engine (services/recommendation_service.py)
  ├── Budget Allocation Engine (services/budget_service.py)
  ├── Location & 60 KM Service (services/location_service.py)
  ├── Travel Estimation Service (services/travel_service.py)
  ├── Product Scanner Service (services/product_scan_service.py)
  ├── Price Comparison Engine (services/price_comparison_service.py)
  │
  ├── Gemini AI Service (services/gemini_service.py)
  │     ├── Text-based LLM recommendations
  │     └── Multimodal Vision (Outfit analysis & Product identification)
  │
  └── Platform Adapters (services/platforms/)
        ├── Amazon (Amazon India verified search URLs)
        ├── Flipkart (Flipkart verified search URLs)
        ├── IKEA (IKEA India search URLs)
        ├── Swiggy (Food/catering search URLs)
        ├── Zomato (Restaurant/caterer search URLs)
        └── OYO (Guest room search URLs)
```

---

## 📁 Directory Structure

```
NM/
├── main.py                          # FastAPI application entrypoint & middleware
├── requirements.txt                 # Project dependencies
├── .env.example                     # Environment configuration template
├── .env                             # Active environment configuration
├── .gitignore                       # Git ignore definitions
├── README.md                        # Documentation
│
├── database/
│   └── database.py                  # SQLite database connection & schema initialization
│
├── models/
│   ├── user.py                      # User registration, login, and session models
│   ├── planner.py                   # Input models for Home, Party, Jewelry planners
│   ├── recommendation.py            # Normalized recommendation structures & summaries
│   └── history.py                   # History and product scan comparison models
│
├── routes/
│   ├── auth.py                      # Authentication endpoints (/login, /register, /logout)
│   ├── home.py                      # Home interior planner routes (/home-planner, /generate-home)
│   ├── party.py                     # Party planner routes (/party-planner, /generate-party)
│   ├── jewelry.py                   # Jewelry planner routes (/jewelry-planner, /generate-jewelry)
│   ├── scanner.py                   # Product price scanner (/scan-product, /api/scan-history)
│   ├── history.py                   # User plan history (/history, /api/history)
│   ├── location.py                  # Location & transit APIs (/api/location/nearby, /api/travel/estimate)
│   └── recommendations.py           # Landing (/), Dashboard (/dashboard), Details (/recommendations-details)
│
├── services/
│   ├── gemini_service.py            # Gemini text & multimodal integration with model fallback
│   ├── recommendation_service.py    # Main recommendation coordinator
│   ├── budget_service.py            # Budget calculation and percentage distribution
│   ├── location_service.py          # Haversine distance, 60 KM rule, Google Maps URL builder
│   ├── travel_service.py            # Transit time and cost estimation (Car, Bike, Public)
│   ├── product_scan_service.py      # Camera capture, image handling, product classification
│   ├── price_comparison_service.py  # In-store physical price vs online price engine
│   └── platforms/
│       ├── __init__.py
│       ├── amazon.py                # Amazon India adapter
│       ├── flipkart.py              # Flipkart adapter
│       ├── ikea.py                  # IKEA India adapter
│       ├── swiggy.py                # Swiggy catering adapter
│       ├── zomato.py                # Zomato dining/caterer adapter
│       └── oyo.py                   # OYO room accommodation adapter
│
├── templates/                       # Jinja2 HTML templates
│   ├── base.html                    # Base layout with Google Fonts & responsive navigation
│   ├── index.html                   # Landing page
│   ├── login.html                   # Login view
│   ├── register.html                # Registration view
│   ├── dashboard.html               # User dashboard with quick tools & statistics
│   ├── home_planner.html            # Home interior planning form
│   ├── home_recommendations.html    # Home interior recommendation results
│   ├── party_planner.html           # Party budget planning form with geolocation
│   ├── party_recommendations.html   # Party venue recommendations with 60 KM badge & transit
│   ├── jewelry_planner.html         # Jewelry planner form with optional outfit upload
│   ├── jewelry_recommendations.html # Jewelry recommendations results
│   ├── recommendation_details.html  # Item & plan inspection view
│   ├── history.html                 # Saved budget plans and scanned items history
│   └── scan_product.html            # In-store camera scanner & comparison table
│
├── static/
│   ├── css/
│   │   ├── main.css                 # Core design system & layout
│   │   └── components.css           # Cards, budget meters, camera viewport, comparison table
│   └── js/
│       ├── main.js                  # Formatting and alert helpers
│       ├── location.js              # Browser geolocation trigger & permission handling
│       └── scanner.js               # Camera capture to canvas & file fallback
│
├── uploads/                         # Stored user-uploaded images (.gitkeep preserved)
│
├── tests/                           # Automated Pytest suite
│   ├── test_pocketsmart.py          # Core unit & integration tests
│   └── test_extended.py             # Validation and edge-case tests
│
└── scripts/
    └── e2e_verify.py                # Live HTTP end-to-end verification script
```

---

## ⚙️ Environment Variables (`.env`)

Configure the `.env` file in the project root:

```env
# Gemini AI Configuration
# Get an API key from Google AI Studio (https://aistudio.google.com/)
GEMINI_API_KEY=
# Configurable model (defaults to gemini-2.5-flash with fallback to gemini-2.0-flash / gemini-1.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Application Security
SECRET_KEY=pocketsmart_super_secret_session_key_change_in_production_2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=sqlite:///./pocketsmart.db

# Configurable Travel & Distance Rates (INR per KM)
CAR_COST_PER_KM=12.0
BIKE_COST_PER_KM=4.5
PUBLIC_TRANSPORT_ESTIMATE=2.0

# Optional Google APIs (App degrades gracefully using OpenStreetMap/Haversine if not set)
GOOGLE_MAPS_API_KEY=
GOOGLE_PLACES_API_KEY=
GOOGLE_ROUTES_API_KEY=

# Settings
APP_NAME="PocketSmart AI"
APP_ENV=development
DEBUG=True
DEMO_MODE=true
```

> **Note on Third-Party Credentials**:
> If `GEMINI_API_KEY` is not provided, the application runs in robust offline fallback mode with verified domain catalog adapters. Adding a valid Gemini API key enables live multimodal vision analysis for outfit styling and physical store barcode/product package inspection.

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
- Python 3.12 or later installed.
- Recommended: `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh` or installed via PowerShell).

### 2. Environment Setup
```powershell
# Create virtual environment with Python 3.12
uv venv --python 3.12 .venv

# Activate virtual environment
.\.venv\Scripts\activate
```

### Quick Launch Options

You can start the development server using any of the following methods:

**Option A (NPM)**:
```powershell
npm run dev
```

**Option B (One-Click Windows Script)**:
```powershell
.\run.bat
```

**Option C (Direct Python Virtual Environment)**:
```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at **`http://127.0.0.1:8000`**.

---

## 🧪 Testing & Verification

PocketSmart AI includes comprehensive automated test suites and a live HTTP end-to-end runner.

### Run Automated Unit & Integration Tests (Pytest)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
All 13 test cases validate:
- User registration, duplicate checks, login, and session cookie lifecycle.
- Budget allocation across categories for Home, Party, and Jewelry planners.
- 60 KM nearby venue discovery, distance, and transit calculations.
- Product price scanning, shipping cost additions, and savings calculations.
- User data isolation in history logs.
- Graceful handling of venues without official websites.

### Run Live End-to-End HTTP Verification
With the server running on `http://127.0.0.1:8000`:
```powershell
.\.venv\Scripts\python.exe scripts\e2e_verify.py
```
This tests all 12 key user flows over live HTTP sockets and confirms 100% pass rates.

---

## 🔒 Security Best Practices Implemented
- **Password Hashing**: Cryptographic PBKDF2-HMAC-SHA256 with random salt; no plain-text passwords stored or returned.
- **Session Protection**: HTTP-only, `SameSite=Lax` session cookies with expiration checks.
- **Credential Safety**: Zero hardcoded API keys. All keys read from server-side environment variables.
- **SQL Injection Prevention**: 100% parameterized SQL queries across all database operations.
- **User Isolation**: Explicit `user_id` filtering on all history, plan, and product scan queries.
- **XSS & Link Security**: All external links use `rel="noopener noreferrer"`. No `javascript:void(0)` or `#` placeholder links.
