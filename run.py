# run.py
import os
import sys
from pathlib import Path
import uvicorn

from dotenv import load_dotenv
if Path(".env").is_file():
    print("📝 Loading environment variables from .env file...")
    load_dotenv()
else:
    print("⚠️ .env file not found. Using system environment variables or defaults.")

# Corrected import from settings
from config.settings import AIF_HOST, AIF_PORT, UVICORN_RELOAD_MODE, APP_DEBUG_MODE
from app.core.key_manager import load_keys as initialize_aif_keys
from app.db.mongo_client import get_db, ensure_db_indexes
# app needs to be imported after dotenv and settings for create_app to get env vars
from app import create_app


def setup_project_directories():
    print("📁 Setting up project directories...")
    Path(os.getenv("AIF_LOGS_DIR", "logs")).mkdir(parents=True, exist_ok=True)
    Path(os.getenv("AIF_DATA_DIR", "data")).mkdir(parents=True, exist_ok=True)
    print("✅ Project directories ensured.")

def check_critical_environment_vars():
    print("🔍 Checking critical environment variables...")
    # Using APP_DEBUG_MODE for this check
    if not APP_DEBUG_MODE and "localhost" in os.getenv("AIF_DATABASE_URL", ""):
        print("⚠️ WARNING: Running in non-debug mode with a MongoDB URL pointing to localhost.")
    # Check for FLASK_SECRET_KEY (now from settings.py)
    from config.settings import FLASK_SECRET_KEY # Import it here or ensure it's handled in settings
    if FLASK_SECRET_KEY == 'a-very-secret-key-for-dev-only-change-me' and not APP_DEBUG_MODE:
        print("CRITICAL ⚠️: Default FLASK_SECRET_KEY is being used in a non-debug environment! Change this in .env or settings.py.")
        # Consider exiting if this is a hard requirement for non-debug: sys.exit(1)
    print("✅ Environment variable check (basic) complete.")

def initialize_dependencies():
    print("⚙️ Initializing critical dependencies...")
    try:
        initialize_aif_keys()
        db_instance = get_db()
        ensure_db_indexes(db_instance)
        print("✅ Dependencies initialized successfully.")
    except Exception as e:
        print(f"❌ CRITICAL FAILURE during dependency initialization: {e}")
        print("   Application cannot start. Please check configurations and external services.")
        sys.exit(1)

def main():
    print("🚀 Starting NeuProtocol AIF Core Service...")

    setup_project_directories()
    check_critical_environment_vars()
    initialize_dependencies()

    print(f"🌐 AIF Core Service attempting to start on http://{AIF_HOST}:{AIF_PORT}")
    # Using UVICORN_RELOAD_MODE for uvicorn's reload flag
    print(f"🐛 Reload mode: {UVICORN_RELOAD_MODE} (App Debug Mode: {APP_DEBUG_MODE})")

    uvicorn.run(
        "app:create_app",
        host=AIF_HOST,
        port=AIF_PORT,
        reload=UVICORN_RELOAD_MODE, # Use the correct variable
        factory=True,
        log_level="info" if not APP_DEBUG_MODE else "debug" # Use APP_DEBUG_MODE for log_level
    )

if __name__ == "__main__":
    main()