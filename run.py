# run.py - Render Deployment Script
import os
import sys
from pathlib import Path
import uvicorn
import logging

# Try to load .env file for local development convenience.
# On Render, environment variables will be set directly in the dashboard.
from dotenv import load_dotenv
if Path(".env").is_file():
    print("📝 Loading environment variables from .env file...")
    load_dotenv()
else:
    print("ℹ️ .env file not found. Using system environment variables (expected for Render deployment).")

# Setup basic logging for the startup script
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: [%(asctime)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AIF_Core_Service_Runner")

# Import settings AFTER potential dotenv load
from config.settings import (
    AIF_HOST, 
    AIF_PORT, 
    UVICORN_RELOAD_MODE, 
    APP_DEBUG_MODE,
    SESSION_SECRET_KEY,
    JWT_SECRET_KEY,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET
)
from app.core.key_manager import load_keys as initialize_aif_keys
from app.db.mongo_client import get_db, ensure_db_indexes
# app needs to be imported after dotenv and settings for create_app to get env vars
from app import create_app

def setup_project_directories():
    """Ensure basic operational directories exist."""
    logger.info("📁 Setting up project directories...")
    try:
        # Create necessary directories
        Path(os.getenv("AIF_LOGS_DIR", "logs")).mkdir(parents=True, exist_ok=True)
        Path(os.getenv("AIF_DATA_DIR", "data")).mkdir(parents=True, exist_ok=True)
        logger.info("✅ Project directories ensured.")
    except Exception as e:
        logger.warning(f"⚠️ Warning setting up directories: {e}")

def check_critical_environment_vars():
    """Check for critical environment variables, especially for production deployment."""
    logger.info("🔍 Checking critical environment variables...")
    
    # Check database URL for production concerns
    database_url = os.getenv("AIF_DATABASE_URL", "")
    if not APP_DEBUG_MODE and ("localhost" in database_url or "127.0.0.1" in database_url):
        logger.warning("⚠️ WARNING: Running in production mode with a MongoDB URL pointing to localhost.")
    
    # Check session secret key
    if SESSION_SECRET_KEY == 'session-secret-key-change-me-in-production':
        if not APP_DEBUG_MODE:
            logger.critical("❌ CRITICAL: Default SESSION_SECRET_KEY is being used in production! Change this in environment variables.")
            sys.exit(1)
        else:
            logger.warning("⚠️ WARNING: Using default SESSION_SECRET_KEY in debug mode.")
    
    # Check JWT secret key
    if JWT_SECRET_KEY == 'jwt-secret-key-change-me-in-production':
        if not APP_DEBUG_MODE:
            logger.critical("❌ CRITICAL: Default JWT_SECRET_KEY is being used in production! Change this in environment variables.")
            sys.exit(1)
        else:
            logger.warning("⚠️ WARNING: Using default JWT_SECRET_KEY in debug mode.")
    
    # Check GitHub OAuth credentials
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        logger.error("❌ ERROR: GitHub OAuth credentials not configured. Authentication will not work.")
        if not APP_DEBUG_MODE:
            logger.critical("❌ CRITICAL: GitHub OAuth is required for production deployment.")
            sys.exit(1)
    
    # Legacy Flask secret key check
    try:
        from config.settings import FLASK_SECRET_KEY
        if FLASK_SECRET_KEY == 'a-very-secret-key-for-dev-only-change-me' and not APP_DEBUG_MODE:
            logger.critical("❌ CRITICAL: Default FLASK_SECRET_KEY is being used in production! Change this in environment variables.")
            sys.exit(1)
    except ImportError:
        pass  # FLASK_SECRET_KEY might not be defined in settings
    
    logger.info("✅ Environment variable check complete.")

def initialize_dependencies():
    """Initialize critical dependencies like keys and database."""
    logger.info("⚙️ Initializing critical dependencies...")
    try:
        # Initialize cryptographic keys
        initialize_aif_keys()
        logger.info("   ✅ Cryptographic keys initialized.")
        
        # Initialize database connection and indexes
        db_instance = get_db()
        ensure_db_indexes(db_instance)
        logger.info("   ✅ Database connection and indexes initialized.")
        
        logger.info("✅ Dependencies initialized successfully.")
    except Exception as e:
        logger.critical(f"❌ CRITICAL FAILURE during dependency initialization: {e}", exc_info=True)
        logger.critical("   Application cannot start. Please check configurations and external services.")
        sys.exit(1)

def get_render_host_port():
    """Get host and port configuration for Render deployment."""
    # Render automatically sets the PORT environment variable
    # Host should be 0.0.0.0 for Render to properly route traffic
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", AIF_PORT))
    
    # Override local settings for Render deployment
    if os.getenv("RENDER"):
        host = "0.0.0.0"
        # Use Render's PORT if available, otherwise fall back to AIF_PORT
        port = int(os.getenv("PORT", port))
    
    return host, port

def main():
    """Main application startup sequence for Render deployment."""
    logger.info("🚀 Starting NeuProtocol AIF Core Service for Render deployment...")

    setup_project_directories()
    check_critical_environment_vars()
    initialize_dependencies()

    # Get host and port for Render
    host, port = get_render_host_port()
    
    # For production deployment, reload should be disabled
    reload_mode = UVICORN_RELOAD_MODE if APP_DEBUG_MODE else False
    
    logger.info(f"🌐 AIF Core Service configured to start on http://{host}:{port}")
    logger.info(f"🔄 Uvicorn Reload mode: {reload_mode}")
    logger.info(f"🐛 Application Debug Mode: {APP_DEBUG_MODE}")
    logger.info(f"🌍 Render Environment: {'Yes' if os.getenv('RENDER') else 'No'}")

    try:
        uvicorn.run(
            "app:create_app",
            host=host,
            port=port,
            reload=reload_mode,
            factory=True,
            log_level="info" if not APP_DEBUG_MODE else "debug",
            # Additional Render-friendly settings
            access_log=True,
            use_colors=False,  # Render logs work better without color codes
            server_header=False,  # Remove server header for security
            date_header=False  # Remove date header to reduce log noise
        )
    except Exception as e:
        logger.critical(f"❌ Failed to start uvicorn server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()