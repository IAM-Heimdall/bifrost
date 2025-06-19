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
    # === OpenAI Models (Latest Generation) ===
    "gpt-4.1",                           # Latest, best coding performance
    "gpt-4.1-mini",                      # Fast and efficient
    "gpt-4.1-nano",                      # Fastest and cheapest
    "gpt-4o",                            # Flagship multimodal model
    "gpt-4o-mini",                       # Cost-effective multimodal
    "gpt-4-turbo",                       # Previous generation (maintained for compatibility)
    "gpt-3.5-turbo",                     # Efficient general purpose
    "o3",                                # Advanced reasoning model
    "o3-mini",                           # Efficient reasoning model
    "o1-preview",                        # Previous reasoning model
    "o1-mini",                           # Previous reasoning model (small)
    
    # === Anthropic Claude Models ===
    "claude-sonnet-4-20250514",          # Latest Claude 4 generation
    "claude-opus-4",                     # Most capable Claude 4
    "claude-3.7-sonnet",                 # Hybrid reasoning model
    "claude-3.5-sonnet-20241022",        # Enhanced coding capabilities
    "claude-3.5-haiku-20241022",         # Fast and efficient
    "claude-3-opus-20240229",            # Previous flagship (maintained for compatibility)
    "claude-3-sonnet-20240229",          # Previous balanced (maintained for compatibility)
    "claude-3-haiku-20240307",           # Previous fast (maintained for compatibility)
    
    # === Google Gemini Models ===
    "gemini-2.5-pro-experimental",       # Most advanced with reasoning
    "gemini-2.5-flash",                  # Balanced performance with thinking
    "gemini-2.0-flash",                  # Production ready workhorse
    "gemini-2.0-flash-lite",             # Cost-efficient option
    "gemini-2.0-pro-experimental",       # Enhanced coding and complex prompts
    "gemini-1.5-pro-latest",             # Previous generation (maintained for compatibility)
    "gemini-1.5-flash-latest",           # Previous generation efficient
    
    # === xAI Models ===
    "grok-3",                            # Latest reasoning model, math/science
    "grok-2",                            # Previous generation
    "grok-1.5",                          # Earlier version
    
    # === Meta Llama Models (Open Source) ===
    # Llama 4 Generation
    "llama-4-scout-17b",                 # 16 experts, 10M context
    "llama-4-maverick-17b",              # 128 experts, 1M context
    
    # Llama 3.3 Generation  
    "llama-3.3-70b",                     # More efficient than 3.1
    "llama-3.3-70b-instruct",            # Instruction-tuned
    
    # Llama 3.2 Generation
    "llama-3.2-90b-vision",              # Large multimodal vision
    "llama-3.2-11b-vision",              # Smaller vision model
    "llama-3.2-3b",                      # Edge/mobile optimized
    "llama-3.2-1b",                      # Lightweight edge
    "llama-3.2-3b-instruct",             # Instruction-tuned 3B
    "llama-3.2-1b-instruct",             # Instruction-tuned 1B
    
    # Llama 3.1 Generation
    "llama-3.1-405b",                    # Largest open source
    "llama-3.1-405b-instruct",           # Instruction-tuned 405B
    "llama-3.1-70b",                     # High performance
    "llama-3.1-70b-instruct",            # Instruction-tuned 70B
    "llama-3.1-8b",                      # Efficient general use
    "llama-3.1-8b-instruct",             # Instruction-tuned 8B
    
    # Legacy Llama (maintained for compatibility)
    "meta-llama/Meta-Llama-3-70B-Instruct",  # Previous naming format
    "llama-3-70b-instruct",              # Standard naming
    "llama-3-8b-instruct",               # Standard naming
    
    # === Mistral Models ===
    # Latest Generation
    "mistral-large-2",                   # 123B parameter flagship
    "pixtral-large",                     # 124B multimodal extension
    "mistral-medium-3",                  # Latest efficient model
    "mistral-small-3.1",                # Compact efficient option
    
    # Reasoning Models
    "magistral-medium",                  # First reasoning from Mistral
    "magistral-small-24b",               # Open source reasoning
    
    # Specialized Models
    "mistral-nemo-12b",                  # Multilingual, 128k context
    "codestral-22b",                     # Code generation specialist
    "codestral-mamba-7b",                # Mamba architecture for code
    "mathstral-7b",                      # Mathematics specialist
    
    # Core Models
    "mistral-7b-v0.3",                  # Latest 7B foundation
    "mistral-7b-instruct-v0.3",         # Instruction-tuned
    "mixtral-8x7b-instruct-v0.1",       # Mixture of experts (maintained for compatibility)
    "mixtral-8x22b-instruct-v0.1",      # Larger mixture model
    
    # Legacy naming (maintained for compatibility)
    "mistralai/Mistral-7B-Instruct-v0.2",  # Previous naming format
    "mistralai/Mixtral-8x7B-Instruct-v0.1", # Previous naming format
    
    # === Chinese AI Models ===
    # Alibaba Qwen Series
    "qwen-2.5-max",                      # MoE flagship
    "qwen-2.5-72b-instruct",            # Large general purpose
    "qwen-2.5-32b-instruct",            # Mid-size efficient
    "qwen-2.5-14b-instruct",            # Balanced performance
    "qwen-2.5-7b-instruct",             # Popular general purpose
    "qwen-2.5-3b-instruct",             # Lightweight
    "qwen-2.5-1.5b-instruct",           # Ultra-lightweight
    "qwen-2.5-coder-32b",               # Code specialist
    "qwen-2.5-math-72b",                # Mathematics specialist
    "qwen-2.5-vl-72b",                  # Vision-language
    
    # DeepSeek Models
    "deepseek-r1",                       # Reasoning model
    "deepseek-v3",                       # Latest generation
    "deepseek-coder-v2-236b",           # Code specialist
    "deepseek-coder-33b-instruct",      # Smaller coding model
    "deepseek-math-7b",                 # Mathematics specialist
    "deepseek-chat",                     # Conversational
    
    # Other Chinese Models
    "yi-34b-chat",                      # 01.AI bilingual
    "yi-6b-chat",                       # Smaller 01.AI
    "baichuan2-13b-chat",               # Baichuan conversational
    "chatglm3-6b",                      # Zhipu AI
    "internlm2-20b",                    # Shanghai AI Lab
    
    # === Cohere Models ===
    "command-r-plus",                    # Flagship (maintained for compatibility)
    "command-r",                         # Balanced option
    "command-light",                     # Lightweight
    "command-nightly",                   # Latest experimental
    
    # === Microsoft Models ===
    "phi-3.5-mini-instruct",            # Latest efficient model
    "phi-3.5-moe-instruct",             # Mixture of experts
    "phi-3-medium-instruct",            # Mid-size option
    "microsoft/phi-2",                   # Legacy naming (maintained for compatibility)
    "orca-2-13b",                       # Reasoning on Llama
    "orca-2-7b",                        # Smaller Orca
    
    # === Open Source Community Models ===
    # Large Models
    "bloom-176b",                        # Multilingual collaborative
    "falcon-180b",                       # Ultra-large open
    "falcon-40b",                        # Mid-size Falcon
    "falcon-7b",                         # Efficient Falcon
    
    # Popular Community Models
    "starling-lm-7b-alpha",             # RLHF optimized
    "openchat-3.5-0106",                # Conversation optimized (maintained for compatibility)
    "zephyr-7b-beta",                   # Helpful assistant
    "vicuna-13b-v1.5",                  # Popular assistant
    "vicuna-7b-v1.5",                   # Smaller Vicuna
    "wizardlm-70b-v1.0",                # Instruction specialist
    "wizardlm-13b-v1.2",                # Smaller WizardLM
    "alpaca-7b",                        # Stanford instruction
    
    # Legacy naming (maintained for compatibility)
    "HuggingFaceH4/zephyr-7b-alpha",    # Previous naming format
    "openchat/openchat-3.5-0106",       # Previous naming format
    
    # Code Specialists
    "code-llama-34b-instruct",          # Meta code specialist
    "code-llama-13b-instruct",          # Smaller code model
    "code-llama-7b-instruct",           # Compact code model
    "wizardcoder-34b-v1.0",             # Code generation
    "starcoder2-15b",                   # BigCode latest
    "starcoder2-7b",                    # Smaller StarCoder
    
    # === AI21 Models ===
    "jurassic-2-ultra",                  # AI21 flagship
    "jurassic-2-mid",                    # Mid-tier
    "jurassic-2-light",                  # Lightweight
    
    # === Stability AI Models ===
    "stable-code-3b",                    # Code generation
    "stablelm-2-12b",                   # General purpose
    "stablelm-2-1.6b",                  # Lightweight
    
    # === Multimodal Specialists ===
    "llava-1.6-34b",                   # Large vision-language
    "llava-1.6-13b",                   # Mid-size vision-language
    "llava-1.6-7b",                    # Compact vision-language
    "blip2-flan-t5-xl",                 # Vision-language understanding
    "instructblip-7b",                  # Instruction-following vision
    "minigpt-4",                        # Compact multimodal
    
    # === Alternative Architectures ===
    "rwkv-4-7b",                        # Alternative architecture
    "mamba-2.8b",                       # State space model
    "retnet-7b",                        # Alternative to transformer
    "jamba-instruct",                   # Hybrid Mamba-Transformer
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