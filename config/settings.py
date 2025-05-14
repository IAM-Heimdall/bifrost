# config/settings.py
import os
from pathlib import Path
from typing import List, Dict, Optional

# --- Core AIF Service Configuration ---
CORE_AIF_SERVICE_ISSUER_ID: str = os.getenv("AIF_CORE_ISSUER_ID", "aif://poc-heimdall.example.com")
DEFAULT_TOKEN_EXPIRY_MINUTES: int = int(os.getenv("AIF_DEFAULT_TOKEN_EXPIRY_MINUTES", "15"))

# --- Key Management Configuration ---
KEYS_DIR_CONFIG: str = os.getenv("AIF_KEYS_DIR", "keys_poc") # Changed from "keys" to avoid conflict
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
KEYS_DIR = PROJECT_ROOT_DIR / KEYS_DIR_CONFIG
KEY_ID: str = os.getenv("AIF_KEY_ID", "poc-heimdall-key-01")
ALGORITHM: str = "EdDSA"

# --- Database Configuration ---
MONGO_DATABASE_URL: str = os.getenv("AIF_DATABASE_URL", "mongodb://localhost:27017/")
MONGO_DATABASE_NAME: str = os.getenv("AIF_DATABASE_NAME", "aif_core_service_poc_db")
REVOKED_TOKENS_COLLECTION_NAME: str = "revoked_atks"

# --- AI Model Configuration ---
SUPPORTED_AI_MODELS: List[str] = [
    "gpt-4-turbo",                            # OpenAI
    "gpt-3.5-turbo",                          # OpenAI
    "claude-3-opus-20240229",                # Anthropic
    "claude-3-sonnet-20240229",              # Anthropic
    "gemini-1.5-pro-latest",                 # Google DeepMind
    "meta-llama/Meta-Llama-3-70B-Instruct",  # Meta (LLaMA 3)
    "mistralai/Mistral-7B-Instruct-v0.2",     # Mistral
    "mistralai/Mixtral-8x7B-Instruct-v0.1",   # Mistral (MoE)
    "command-r-plus",                         # Cohere
    "HuggingFaceH4/zephyr-7b-alpha",          # Hugging Face
    "openchat/openchat-3.5-0106",             # Hugging Face (OpenChat)
    "microsoft/phi-2"                         # Microsoft
]

# --- PERMISSION CONFIGURATION ---
# Defines a list of known/standardized permission strings the IE can issue.
# ABs/UI will select from these or provide custom ones (which IE might validate/log).
STANDARD_PERMISSIONS_LIST: List[str] = [
    "read:articles_all",
    "read:articles_topic_tech",
    "read:user_profile_basic",
    "summarize:text_content_short",
    "summarize:text_content_long",
    "analyze:sentiment_text",
    "interact:chatbot_basic",
    "kms:read_secret_group_A",
    # Add more standard permissions as concepts develop
]

# --- (OPTIONAL) Minimal Default Trust Tags for Phase 1 ---
# These are actual trust/metadata attributes, not permissions.
# If None, the aif_trust_tags claim can be omitted from the ATK.
DEFAULT_AIF_TRUST_TAGS: Optional[Dict[str, str]] = {
    "issuer_assurance": "poc_development_level",
    "agent_environment": "simulated_user_poc" # Indicates the user context is simulated for PoC
}
# To disable trust tags entirely for initial PoC, set this to None:
# DEFAULT_AIF_TRUST_TAGS: Optional[Dict[str, str]] = None

# List of *allowed keys* for any trust tags if they are provided in requests,
# preventing arbitrary tags. Values can be free-form for PoC or also restricted.
ALLOWED_TRUST_TAG_KEYS: List[str] = [
    "user_verification_level", # e.g., "simulated_user_poc", "email_verified_via_ie"
    "issuer_assurance",        # e.g., "poc_development_level", "tier1_partner"
    "agent_environment",       # e.g., "agent_builder_platform_X", "user_direct_invocation"
    "data_processing_region"   # e.g., "EU", "US"
]


# --- Server Configuration (for run.py) ---
AIF_HOST: str = os.getenv('AIF_HOST', '127.0.0.1')
AIF_PORT: int = int(os.getenv('AIF_PORT', '5000'))
# Use specific UVICORN_RELOAD for clarity, or derive from a general DEBUG_MODE
UVICORN_RELOAD_MODE: bool = os.getenv('UVICORN_RELOAD', "true").lower() == 'true'
APP_DEBUG_MODE: bool = os.getenv('APP_DEBUG_MODE', "true").lower() == 'true' # For general app debug logging

FLASK_SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', 'a-very-secret-key-for-dev-only-change-me')
if FLASK_SECRET_KEY == 'a-very-secret-key-for-dev-only-change-me' and not APP_DEBUG_MODE:
    print("⚠️ WARNING: FLASK_SECRET_KEY is set to a default development value in a non-debug environment!")