import os
from pathlib import Path
from typing import List, Dict, Optional

# --- Core AIF Service Configuration ---
CORE_AIF_SERVICE_ISSUER_ID: str = os.getenv("AIF_CORE_ISSUER_ID", "aif://poc-heimdall.example.com")
DEFAULT_TOKEN_EXPIRY_MINUTES: int = int(os.getenv("AIF_DEFAULT_TOKEN_EXPIRY_MINUTES", "15"))

# --- Server Configuration ---
AIF_HOST: str = os.getenv('AIF_HOST', '127.0.0.1')
AIF_PORT: int = int(os.getenv('AIF_PORT', '5000'))
UVICORN_RELOAD_MODE: bool = os.getenv('UVICORN_RELOAD', "true").lower() == 'true'
APP_DEBUG_MODE: bool = os.getenv('APP_DEBUG_MODE', "true").lower() == 'true'

# --- Key Management Configuration ---
KEYS_DIR_CONFIG: str = os.getenv("AIF_KEYS_DIR", "keys_poc")
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
KEYS_DIR = PROJECT_ROOT_DIR / KEYS_DIR_CONFIG
KEY_ID: str = os.getenv("AIF_KEY_ID", "poc-heimdall-key-01")
ALGORITHM: str = "EdDSA"

# --- Database Configuration ---
MONGO_DATABASE_URL: str = os.getenv("AIF_DATABASE_URL", "mongodb://localhost:27017/")
MONGO_DATABASE_NAME: str = os.getenv("AIF_DATABASE_NAME", "aif_core_service_poc_db")
REVOKED_TOKENS_COLLECTION_NAME: str = "revoked_atks"
USERS_COLLECTION_NAME: str = "users"
ISSUED_TOKENS_COLLECTION_NAME: str = "issued_tokens"

# --- AI Model Configuration ---
SUPPORTED_AI_MODELS: List[str] = [
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "gemini-1.5-pro-latest",
    "meta-llama/Meta-Llama-3-70B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "command-r-plus",
    "HuggingFaceH4/zephyr-7b-alpha",
    "openchat/openchat-3.5-0106",
    "microsoft/phi-2"
]

# --- PERMISSION CONFIGURATION ---
STANDARD_PERMISSIONS_LIST: List[str] = [
    "read:articles_all",
    "read:articles_topic_tech",
    "read:user_profile_basic",
    "summarize:text_content_short",
    "summarize:text_content_long",
    "analyze:sentiment_text",
    "interact:chatbot_basic",
    "kms:read_secret_group_A",
]

# --- Trust Tags Configuration ---
DEFAULT_AIF_TRUST_TAGS: Optional[Dict[str, str]] = {
    "issuer_assurance": "poc_development_level",
    "agent_environment": "simulated_user_poc"
}

ALLOWED_TRUST_TAG_KEYS: List[str] = [
    "user_verification_level",
    "issuer_assurance",
    "agent_environment",
    "data_processing_region"
]

# --- Authentication Configuration ---
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-me-in-production")
SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "session-secret-key-change-me-in-production")
BASE_URL: str = os.getenv("BASE_URL", f"http://{AIF_HOST}:{AIF_PORT}")

# --- Application Security ---
FLASK_SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', 'a-very-secret-key-for-dev-only-change-me')

# --- Configuration warnings ---
if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    print("⚠️ WARNING: GitHub OAuth credentials not configured. Authentication will not work.")

if JWT_SECRET_KEY == "jwt-secret-key-change-me-in-production" and not APP_DEBUG_MODE:
    print("⚠️ WARNING: Default JWT secret key is being used in non-debug mode!")

if SESSION_SECRET_KEY == "session-secret-key-change-me-in-production" and not APP_DEBUG_MODE:
    print("⚠️ WARNING: Default session secret key is being used in non-debug mode!")

if FLASK_SECRET_KEY == 'a-very-secret-key-for-dev-only-change-me' and not APP_DEBUG_MODE:
    print("⚠️ WARNING: FLASK_SECRET_KEY is set to a default development value in a non-debug environment!")