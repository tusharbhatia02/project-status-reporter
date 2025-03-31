# api/main.py
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import settings and router
# Use absolute imports from the root 'backend' perspective if running uvicorn from there
# Or relative imports if running from within 'api' context (less common)
try:
    from config.settings import settings
    from api.routes import report_router # Use api.routes for clarity if needed
except ImportError:
     # Fallback for different execution contexts or simpler structures
     from ..config.settings import settings
     from .routes import report_router


# Configure logging basic setup (can be refined further)
log_level = settings.LOG_LEVEL.upper() if settings else "INFO"
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


# Create FastAPI app instance
app_config = {
    "title": "Default Title (Settings Failed)",
    "version": "0.0.0",
    "description": "API to generate project status reports and notify Slack."
}
if settings:
    app_config["title"] = settings.PROJECT_NAME
    app_config["version"] = settings.PROJECT_VERSION

app = FastAPI(**app_config)


# --- CORS Middleware ---
# Ensure this is configured correctly based on your frontend's origin
origins = [
    "http://localhost:3000",
    # Add production frontend origin if applicable
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all standard methods
    allow_headers=["*"], # Allow all headers
)
logger.info(f"CORS configured for origins: {origins}")


# --- Include Routers ---
# Mount the report router
# Using an API prefix is good practice for versioning
api_prefix = "/api/v1" # Or get from settings: settings.API_V1_STR
app.include_router(report_router.router, prefix=api_prefix, tags=["Status Reports"])
logger.info(f"Report router included with prefix: {api_prefix}")


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """ Basic health check / info endpoint. """
    logger.debug("Root endpoint '/' accessed.")
    # Return basic info about the running API
    return {
        "message": f"Welcome to the {app.title}",
        "version": app.version,
        "docs": f"{api_prefix}/docs" # Point to correct docs URL if prefix is used
        }

logger.info(f"{app.title} v{app.version} initialization complete.")

# Note: The uvicorn run command should target this file's 'app' object
# e.g., from the 'backend' directory: uvicorn api.main:app --reload