import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware  # Changed from fastapi.middleware.sessions
from pathlib import Path

# Import key and DB utility functions that need to run at startup
from app.core.key_manager import load_keys
from app.db.mongo_client import get_db, close_db_connection, ensure_db_indexes

# Import API routers - update paths to match your structure
from app.ie_routes import router as ie_router         
from app.reg_routes import router as reg_router       
from app.ui_routes import router as ui_router         
from app.auth.routes import router as auth_router     

# Import settings for session configuration
from config.settings import SESSION_SECRET_KEY, BASE_URL

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
        load_keys()
    except Exception as e:
        logger.critical(f"❌ CRITICAL STARTUP ERROR: Failed to load cryptographic keys: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize keys: {e}") from e

    try:
        logger.info("💾 Attempting to initialize database connection and ensure indexes...")
        db = get_db()
        ensure_db_indexes(db)
        
        # ADD THIS LINE for revocation indexes:
        from app.db.mongo_client import ensure_revocation_indexes
        ensure_revocation_indexes(db)
        
    except Exception as e:
        logger.critical(f"❌ CRITICAL STARTUP ERROR: Failed to connect to database or ensure indexes: {e}", exc_info=True)
        raise RuntimeError(f"Database initialization failed: {e}") from e

    # --- Create FastAPI App Instance ---
    app = FastAPI(
        title="IAM Heimdall - Agent Identity Framework",
        description="Agent Identity Framework - Combined Issuing Entity and Registry.",
        version="0.5.0",
        # OpenAPI tags for better documentation
        openapi_tags=[
            {"name": "Authentication", "description": "GitHub OAuth and user management."},
            {"name": "UI (PoC Management)", "description": "User interface for PoC operations."},
            {"name": "Issuing Entity (IE)", "description": "Endpoints for ATK issuance."},
            {"name": "Registry (REG)", "description": "Endpoints for key discovery and revocation checking."},
        ]
    )

    # --- Add Session Middleware for Authentication ---
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET_KEY,
        max_age=7 * 24 * 60 * 60,  # 7 days
        same_site="lax",
        https_only=False  # Set to True in production with HTTPS
    )
    logger.info("🔒 Session middleware configured.")

    # --- Mount Static Files (For UI) ---
    static_dir_path = BASE_DIR / "static"
    static_dir_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir_path), name="static")
    logger.info(f"🔩 Static files mounted from: {static_dir_path}")

    # --- Include API Routers ---
    
    # Authentication routes
    app.include_router(auth_router)
    logger.info("🔐 Authentication routes included (/auth/*).")
    
    # UI routes
    app.include_router(ui_router)
    logger.info("🧩 UI routes included under /ui/*.")

    # IE API routes with authentication
    app.include_router(ie_router, prefix="/api/v1")
    logger.info("🧩 Issuing Entity (IE) API routes included under /api/v1/ie/*.")

    # REG API routes (public endpoints)
    app.include_router(reg_router)
    logger.info("🧩 Registry (REG) API routes included (/.well-known/jwks.json, /reg/*).")

    # --- Define Root Path Redirect ---
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """Redirects the root path ('/') to the verify agents public page."""
        return RedirectResponse(url="/ui/verify", status_code=303)

    # --- Event Handlers ---
    @app.on_event("startup")
    async def startup_event():
        logger.info("✅ AIF Core Service Application startup sequence complete.")
        logger.info(f"🌐 Application running at {BASE_URL}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🚪 AIF Core Service Application shutting down...")
        close_db_connection()
        logger.info("✅ Shutdown complete.")

    logger.info("👍 FastAPI application configured and ready.")
    return app