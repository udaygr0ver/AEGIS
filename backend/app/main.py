import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.auth import init_default_admin
from app.api import auth as auth_router
from app.api import logs as logs_router
from app.api import alerts as alerts_router
from app.api import stats as stats_router
from app.detection.engine import detection_engine
from app.ml.anomaly_detector import anomaly_detector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("siem.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Initializing Database Tables...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    db = SessionLocal()
    try:
        init_default_admin(db)
    finally:
        db.close()

    # Start background detection engine
    logger.info("Starting Detection Engine Background Runner...")
    detection_engine.start()

    yield

    # Shutdown sequence
    logger.info("Stopping Detection Engine...")
    detection_engine.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Security Information and Event Management (SIEM) Analytics API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router, prefix=settings.API_V1_STR)
app.include_router(logs_router.router, prefix=settings.API_V1_STR)
app.include_router(alerts_router.router, prefix=settings.API_V1_STR)
app.include_router(stats_router.router, prefix=settings.API_V1_STR)

# Mount static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard_page():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>SIEM API Online</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>")

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
