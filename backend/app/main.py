from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from app.api.routes import clothing
from app.api.routes import measurements
from app.api.routes import ai_inference
from app.api.routes import uploads
from app.api.routes import reconstructions
from app.api.routes import assets
from app.api.routes import tryon_sessions
from app.services.camera_ws import router as camera_ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "frontend" / "public" / "models"
DATA_DIR = BASE_DIR / "data"
UPLOADS_STATIC_DIR = DATA_DIR / "uploads"
RECON_STATIC_DIR = DATA_DIR / "reconstructions"
CLOTHING_STATIC_DIR = DATA_DIR / "clothing"

app = FastAPI(title="FitScan", version="0.2.0", description="Monolith FastAPI: clothing API + measurement + AI inference")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8000",
        "ws://localhost:5173",
        "ws://localhost:5174",
        "ws://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(clothing.router, prefix="/api", tags=["clothing"])
app.include_router(measurements.router, prefix="/api", tags=["measurements"])
app.include_router(uploads.router, prefix="/api", tags=["uploads"])
app.include_router(reconstructions.router, prefix="/api", tags=["reconstructions"])
app.include_router(assets.router, tags=["assets"])
app.include_router(ai_inference.router, prefix="/api/ai", tags=["AI inference"])
app.include_router(tryon_sessions.router, prefix="/api", tags=["tryon sessions"])
app.include_router(camera_ws_router, prefix="/ws", tags=["camera"])

# Static files (GLB models)
if MODELS_DIR.exists():
    app.mount("/static/models", StaticFiles(directory=str(MODELS_DIR)), name="models")
    logger.info(f"[FitScan] Serving static models from {MODELS_DIR}")
else:
    logger.warning(f"[FitScan] Models dir not found: {MODELS_DIR}")

# Static files (Phase B: user uploads + reconstruction GLBs)
for static_dir, mount_path in (
    (UPLOADS_STATIC_DIR,  "/static/uploads"),
    (RECON_STATIC_DIR,    "/static/reconstructions"),
    (CLOTHING_STATIC_DIR, "/static/clothing"),
):
    if static_dir.exists():
        app.mount(mount_path, StaticFiles(directory=str(static_dir)), name=mount_path.strip("/").replace("/", "_"))
        logger.info(f"[FitScan] Serving {mount_path} from {static_dir}")


@app.get("/")
def root():
    return {"name": "FitScan", "version": "0.2.0", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
