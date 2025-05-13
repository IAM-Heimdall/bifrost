# app/core/key_manager.py
import base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

from config.settings import KEYS_DIR, KEY_ID, ALGORITHM

_private_key_pem: Optional[str] = None
_public_key_pem: Optional[str] = None
_private_key_obj: Optional[ed25519.Ed25519PrivateKey] = None
_jwks: Optional[Dict[str, Any]] = None

PRIVATE_KEY_PATH = KEYS_DIR / "aif_private_key.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "aif_public_key.pem"

# --- Helper functions remain the same: _generate_ed25519_keys_pem, _ensure_keys_exist_on_disk, _extract_jwk_x_coordinate ---
def _generate_ed25519_keys_pem() -> tuple[bytes, bytes]:
    logger.info("🧬 Generating new Ed25519 key pair (PEM)...")
    private_key_obj = ed25519.Ed25519PrivateKey.generate()
    public_key_obj = private_key_obj.public_key()
    private_pem_bytes = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem_bytes = public_key_obj.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    logger.info("✅ Ed25519 key pair generated.")
    return private_pem_bytes, public_pem_bytes

def _ensure_keys_exist_on_disk():
    if not PRIVATE_KEY_PATH.exists() or not PUBLIC_KEY_PATH.exists():
        logger.info(f"🔑 Signing keys not found at {KEYS_DIR}. Attempting generation...")
        KEYS_DIR.mkdir(parents=True, exist_ok=True)
        private_pem_bytes, public_pem_bytes = _generate_ed25519_keys_pem()
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(private_pem_bytes)
        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(public_pem_bytes)
        if os.name != 'nt':
            try:
                PRIVATE_KEY_PATH.chmod(0o600)
                PUBLIC_KEY_PATH.chmod(0o644)
            except OSError as e:
                logger.warning(f"⚠️ Warning: Could not set key file permissions: {e}")
        logger.info(f"✅ New keys saved to {KEYS_DIR}")
    else:
        logger.info(f"🔑 Existing signing keys found at {KEYS_DIR}")

def _extract_jwk_x_coordinate(public_key_pem_str: str) -> str:
    public_key_obj = serialization.load_pem_public_key(public_key_pem_str.encode(), backend=default_backend())
    if not isinstance(public_key_obj, ed25519.Ed25519PublicKey):
        raise ValueError("Public key is not an Ed25519 public key.")
    raw_public_key_bytes = public_key_obj.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return base64.urlsafe_b64encode(raw_public_key_bytes).decode().rstrip('=')
# --- End helper functions ---

def load_keys(force_reload: bool = False):
    """
    Loads EdDSA private and public keys from files and prepares JWKS.
    If keys don't exist, they are generated.
    This function aims to be idempotent for the current process.
    """
    global _private_key_pem, _public_key_pem, _private_key_obj, _jwks

    # Check if all essential globals are already populated in *this process's context*
    if not force_reload and all([_private_key_pem, _public_key_pem, _private_key_obj, _jwks]):
        logger.info("🔑 Keys already loaded and prepared in this process.")
        return

    logger.info(f"🔄 Loading AIF signing keys (force_reload={force_reload})...")
    temp_private_pem: Optional[str] = None
    temp_public_pem: Optional[str] = None
    temp_private_obj: Optional[ed25519.Ed25519PrivateKey] = None
    temp_jwks: Optional[Dict[str, Any]] = None

    try:
        _ensure_keys_exist_on_disk()

        logger.info(f"   Reading private key from: {PRIVATE_KEY_PATH}")
        temp_private_pem = Path(PRIVATE_KEY_PATH).read_text()
        logger.info(f"   Reading public key from: {PUBLIC_KEY_PATH}")
        temp_public_pem = Path(PUBLIC_KEY_PATH).read_text()

        temp_private_obj = serialization.load_pem_private_key(
            temp_private_pem.encode(),
            password=None,
            backend=default_backend()
        )
        if not isinstance(temp_private_obj, ed25519.Ed25519PrivateKey):
            raise ValueError("Loaded private key is not an Ed25519 private key.")
        logger.info("   Private key object loaded.")

        x_coordinate = _extract_jwk_x_coordinate(temp_public_pem)
        temp_jwks = {
            "keys": [{"kty": "OKP", "crv": "Ed25519", "kid": KEY_ID, "alg": ALGORITHM, "use": "sig", "x": x_coordinate}]
        }
        
        # Only assign to globals if all steps were successful
        _private_key_pem = temp_private_pem
        _public_key_pem = temp_public_pem
        _private_key_obj = temp_private_obj
        _jwks = temp_jwks
        logger.info("✅ AIF Keys loaded and JWKS prepared successfully.")

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR loading keys: {e}", exc_info=True)
        # Do not assign globals if there was an error, leave them as they were (likely None)
        raise # Re-raise the exception to halt startup if keys are critical

def get_signing_key() -> Optional[ed25519.Ed25519PrivateKey]:
    if _private_key_obj is None:
        logger.debug("🔑 Signing key object not found, attempting to load keys via get_signing_key...")
        load_keys()
    return _private_key_obj

def get_private_key_pem_str() -> Optional[str]:
    if _private_key_pem is None:
        logger.debug("🔑 Private key PEM string not found, attempting to load keys via get_private_key_pem_str...")
        load_keys()
    return _private_key_pem

def get_jwks() -> Optional[Dict[str, Any]]:
    if _jwks is None:
        logger.debug("🔑 JWKS not found, attempting to load keys via get_jwks...")
        load_keys()
    return _jwks