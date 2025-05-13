# app/__init__.py
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse # For root redirect
from pathlib import Path

# Import key and DB utility functions that need to run at startup
from app.core.key_manager import load_keys
from app.db.mongo_client import get_db, close_db_connection, ensure_db_indexes

# Import API routers
from .ie_routes import router as ie_router
from .reg_routes import router as reg_router # This router should define /.well-known/jwks.json at its root
from .ui_routes import router as ui_router

# Determine base directory for static files and templates
BASE_DIR = Path(__file__).resolve().parent

# Configure basic logging for startup messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(message)s')
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.
    """
    logger.info("🚀 Initializing AIF Core Service application...")

    # --- Critical Initializations ---
    try:
        logger.info("🔑 Attempting to load cryptographic keys...")
        load_keys() # This function now prints its own success/failure and can raise errors
    except Exception as e:
        logger.critical(f"❌ CRITICAL STARTUP ERROR: Failed to load cryptographic keys: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize keys: {e}") from e

    try:
        logger.info("💾 Attempting to initialize database connection and ensure indexes...")
        db = get_db() # Establishes connection if not already
        ensure_db_indexes(db) # Create necessary DB indexes
    except Exception as e:
        logger.critical(f"❌ CRITICAL STARTUP ERROR: Failed to connect to database or ensure indexes: {e}", exc_info=True)
        raise RuntimeError(f"Database initialization failed: {e}") from e

    # --- Create FastAPI App Instance ---
    app = FastAPI(
        title="NeuProtocol AIF Core Service (IE+REG PoC)",
        description="Proof of Concept for Agent Identity Framework - Combined Issuing Entity and Registry.",
        version="0.3.0",
        # You can add OpenAPI tags metadata here if desired
        # openapi_tags=[
        #     {"name": "UI (PoC Management)", "description": "User interface for PoC operations."},
        #     {"name": "Issuing Entity (IE)", "description": "Endpoints for ATK issuance."},
        #     {"name": "Registry (REG)", "description": "Endpoints for key discovery and revocation checking."},
        # ]
    )

    # --- Mount Static Files (For UI) ---
    static_dir_path = BASE_DIR / "static"
    static_dir_path.mkdir(parents=True, exist_ok=True) # Ensure it exists
    app.mount("/static", StaticFiles(directory=static_dir_path), name="static")
    logger.info(f"🔩 Static files mounted from: {static_dir_path}")

    # --- Include API Routers ---
    # UI routes (prefixed with /ui by its own router definition)
    app.include_router(ui_router)
    logger.info("🧩 UI routes included (expected under /ui).")

    # IE API routes (prefixed by /api/v1 by this include_router call)
    app.include_router(ie_router, prefix="/api/v1")
    logger.info("🧩 Issuing Entity (IE) API routes included under /api/v1/ie.")

    # REG API routes
    # We include reg_router without a prefix here.
    # This means routes defined in reg_routes.py (like '/.well-known/jwks.json' or '/reg/revoke-atk')
    # will be available at those paths directly from the application root.
    app.include_router(reg_router)
    logger.info("🧩 Registry (REG) API routes included (e.g., /.well-known/jwks.json, /reg/*).")


    # --- Define Root Path Redirect ---
    @app.get("/", include_in_schema=False)
    async def root_redirect_to_ui():
        """Redirects the root path ('/') to the UI dashboard ('/ui/')."""
        return RedirectResponse(url="/ui/")
    logger.info("↪️ Root path ('/') configured to redirect to '/ui/'.")


    # --- Event Handlers ---
    @app.on_event("startup")
    async def startup_event():
        # Initializations are now done before app creation,
        # but this is a good place for other startup tasks if any.
        logger.info("✅ AIF Core Service Application startup sequence complete.")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🚪 AIF Core Service Application shutting down...")
        close_db_connection() # Cleanly close DB connection
        logger.info("✅ Shutdown complete.")

    logger.info("👍 FastAPI application configured and ready.")
    return app