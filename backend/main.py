import os
from pathlib import Path
import contextlib
import io

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import engine, Base
import models  # import all models so Base knows about them
from seed import seed

# Import routers
from routers import auth, resources, bookings, maintenance

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
JS_DIR = PROJECT_DIR / "js"
CSS_DIR = PROJECT_DIR / "css"

# Create all tables
Base.metadata.create_all(bind=engine)
with contextlib.redirect_stdout(io.StringIO()):
    seed()

app = FastAPI(
    title="Smart Campus Resource Management",
    description="API for managing campus resources, bookings, and maintenance",
    version="1.0.0"
)

# CORS — allow frontend (served from file:// or localhost)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(resources.router)
app.include_router(bookings.router)
app.include_router(maintenance.router)

if JS_DIR.exists():
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")

if CSS_DIR.exists():
    app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")



@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/index.html", include_in_schema=False)
def index_page():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/dashboard.html", include_in_schema=False)
def dashboard_page():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/booking.html", include_in_schema=False)
def booking_page():
    return FileResponse(FRONTEND_DIR / "booking.html")


@app.get("/maintenance.html", include_in_schema=False)
def maintenance_page():
    return FileResponse(FRONTEND_DIR / "maintenance.html")


@app.get("/health")
def health():
    return {"status": "ok", "frontend": FRONTEND_DIR.exists()}
