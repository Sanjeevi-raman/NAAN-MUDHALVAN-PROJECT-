"""
PocketSmart AI - Main Application Entrypoint
FastAPI backend powering Home Interior, Party, Jewelry budget planners,
and real-time physical store product price scanning.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database.database import init_db
from routes.auth import router as auth_router
from routes.home import router as home_router
from routes.party import router as party_router
from routes.jewelry import router as jewelry_router
from routes.scanner import router as scanner_router
from routes.history import router as history_router
from routes.location import router as location_router
from routes.recommendations import router as recommendations_router
from services.auth_service import get_current_user_optional

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pocketsmart")

# Lifespan context manager for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    init_db()
    os.makedirs("uploads", exist_ok=True)
    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title="PocketSmart AI",
    description="Your Smart Budget & Recommendation Assistant for Home Interiors, Parties, Jewelry, and In-Store Price Scanning.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Mount Static Files and Uploads
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

# Mount Routers
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(party_router)
app.include_router(jewelry_router)
app.include_router(scanner_router)
app.include_router(history_router)
app.include_router(location_router)
app.include_router(recommendations_router)

# Global 404 Exception Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(status_code=404, content={"error": "Resource not found"})
    user = get_current_user_optional(request)
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found - PocketSmart AI</title>
            <link rel="stylesheet" href="/static/css/main.css">
        </head>
        <body style="display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;">
            <div>
                <h1 style="font-size:3rem;font-weight:800;color:#1e3a8a;">404</h1>
                <p style="font-size:1.25rem;color:#4b5563;margin-bottom:1.5rem;">Page Not Found</p>
                <a href="/" class="btn btn-primary">Return to PocketSmart AI Home</a>
            </div>
        </body>
        </html>
        """,
        status_code=404
    )

# Global 500 Exception Handler
@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(status_code=500, content={"error": "An internal error occurred."})
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Error - PocketSmart AI</title>
            <link rel="stylesheet" href="/static/css/main.css">
        </head>
        <body style="display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;">
            <div>
                <h1 style="font-size:2.5rem;font-weight:800;color:#dc2626;">System Notice</h1>
                <p style="font-size:1.15rem;color:#4b5563;margin-bottom:1.5rem;">
                    Something unexpected happened while processing your request. Please try again.
                </p>
                <a href="/" class="btn btn-primary">Return Home</a>
            </div>
        </body>
        </html>
        """,
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
