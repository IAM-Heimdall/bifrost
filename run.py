# run.py
import os
import sys
from pathlib import Path
import uvicorn
import logging

# Try to load .env file for local development convenience.
# On Render, environment variables will be set directly.
from dotenv import load_dotenv
if Path(".env").is_file():
    print("📝 Local: Loading environment variables from .env file...")
    load_dotenv()
else:
    print("ℹ️ Local: .env file not found. Relying on system environment variables or defaults.")

# Setup basic logging for run.py itself.
# The log level for the app itself will be set by APP_DEBUG_MODE for uvicorn.
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: [%(asctime)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AIF_Core_Service_Runner")

# Import settings AFTER potential dotenv load
from config.settings import (
    UVICORN_RELOAD_MODE,
    APP_DEBUG_MODE
    # AIF_HOST and AIF_PORT will be determined by Render's environment or defaults
)
from app.core.key_manager import load_keys as initialize_aif_keys_globally
from app.db.mongo_client import get_db, ensure_db_indexes
# The 'app:create_app' string will handle importing 'create_app' from 'app' package

def setup_project_directories():
    """Ensure basic operational directories exist if needed by the application."""
    logger.info("📁 Ensuring operational directories exist...")
    # KEYS_DIR is handled by key_manager using config.settings.KEYS_DIR
    # It's good practice for key_manager itself to create KEYS_DIR if it doesn't exist.
    
    # Example for other dirs if your app explicitly uses them:
    # logs_dir = Path(os.getenv("AIF_LOGS_DIR", "logs"))
    # data_dir = Path(os.getenv("AIF_DATA_DIR", "data"))
    # logs_dir.mkdir(parents=True, exist_ok=True)
    # data_dir.mkdir(parents=True, exist_ok=True)
    # logger.info(f"   Ensured: {logs_dir}, {data_dir}")
    logger.info("✅ Operational directories check complete (primarily handled by modules).")

def check_critical_configurations():
    """Perform checks for critical configurations, especially for non-debug environments."""
    logger.info("🔍 Checking critical configurations...")
    from config.settings import MONGO_DATABASE_URL, FLASK_SECRET_KEY # Import only when needed

    if not APP_DEBUG_MODE:
        if "localhost" in MONGO_DATABASE_URL or "127.0.0.1" in MONGO_DATABASE_URL:
            logger.warning("⚠️ WARNING: Production-like mode (APP_DEBUG_MODE=false) with a MongoDB URL pointing to localhost!")
        if FLASK_SECRET_KEY == 'a-very-secret-key-for-dev-only-change-me':
            logger.critical("❌ CRITICAL: Default FLASK_SECRET_KEY is being used in a non-debug environment! This is insecure. Please set a strong secret in your environment variables.")
            # Consider sys.exit(1) if this is a hard requirement for production
    else:
        logger.info("   Running in App Debug Mode. Some checks are more lenient.")
    logger.info("✅ Critical configuration check complete.")


def initialize_global_dependencies():
    """Initialize global dependencies like keys and DB before app creation by Uvicorn."""
    logger.info("⚙️ Initializing global dependencies (keys, DB connection & indexes)...")
    try:
        initialize_aif_keys_globally() # Ensures keys are loaded/generated
        db_instance = get_db()         # Establishes DB connection
        ensure_db_indexes(db_instance) # Ensures DB indexes are created
        logger.info("✅ Global dependencies initialized successfully.")
    except Exception as e:
        logger.critical(f"❌ CRITICAL FAILURE during global dependency initialization: {e}", exc_info=True)
        logger.critical("   Application might not start correctly or will fail at runtime. Please check configurations and external services (DB, Key file paths/permissions).")
        # We let Uvicorn proceed to try and start the app factory, which will then also fail
        # if these dependencies are truly critical for app creation itself.
        # For a hard stop: sys.exit(1)
        pass # Allow Uvicorn to attempt app creation, app's create_app should also check

def main():
    """Main application startup sequence."""
    logger.info("🚀 Starting NeuProtocol AIF Core Service deployment script...")

    setup_project_directories()
    check_critical_configurations()
    initialize_global_dependencies() # Attempt to initialize early

    # Render sets the PORT env var. HOST should be 0.0.0.0.
    host_to_run = os.getenv("HOST", "0.0.0.0")
    port_to_run = int(os.getenv("PORT", os.getenv("AIF_PORT", "5000"))) # Prefer Render's PORT

    # For Render, reload mode should be false. APP_DEBUG_MODE controls app's internal debugging.
    reload_enabled_by_env = UVICORN_RELOAD_MODE

    logger.info(f"🌐 AIF Core Service configured to start on http://{host_to_run}:{port_to_run}")
    logger.info(f"🔄 Uvicorn Reload mode: {reload_enabled_by_env}")
    logger.info(f"🐛 Application Debug Mode: {APP_DEBUG_MODE}")

    uvicorn.run(
        "app:create_app",  # Tells Uvicorn to find create_app in the 'app' package
        host=host_to_run,
        port=port_to_run,
        reload=reload_enabled_by_env,
        factory=True,      # Indicates that "app:create_app" is a factory function
        log_level="info" if not APP_DEBUG_MODE else "debug" # Uvicorn's log level
    )

if __name__ == "__main__":
    main()