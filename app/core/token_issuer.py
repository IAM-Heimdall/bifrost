# app/core/token_issuer.py
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging # Use logging

import jwt
from jwt.exceptions import InvalidTokenError as JOSEError

from config.settings import (
    DEFAULT_TOKEN_EXPIRY_MINUTES,
    CORE_AIF_SERVICE_ISSUER_ID,
    SUPPORTED_AI_MODELS,
    STANDARD_PERMISSIONS_LIST,
    DEFAULT_AIF_TRUST_TAGS, # New: For default trust tags
    ALLOWED_TRUST_TAG_KEYS   # New: For validating provided override trust tags
)
from .key_manager import get_signing_key, get_private_key_pem_str, KEY_ID, ALGORITHM

logger = logging.getLogger(__name__)

def generate_aid(issuer_id: str, model_id: str, user_id: str) -> str:
    agent_instance_id = str(uuid.uuid4())
    return f"{issuer_id}/{model_id}/{user_id}/{agent_instance_id}"

def create_atk(
    user_id: str,
    audience_sp_id: str,
    permissions: List[str], # These are the actual permissions
    purpose: str,
    model_id: str,
    override_trust_tags: Optional[Dict[str, str]] = None # For actual trust metadata
) -> Optional[str]:
    issuer_id_to_use = CORE_AIF_SERVICE_ISSUER_ID
    expiry_minutes_to_use = DEFAULT_TOKEN_EXPIRY_MINUTES

    # OPTION A: Try with the PEM string first
    private_key_pem_str = get_private_key_pem_str() # Get the PEM string from key_manager
    if not private_key_pem_str:
        logger.error("❌ CRITICAL Error: Private key PEM string not available for creating ATK.")
        return None

    # OPTION B: Keep using the key object if A doesn't work
    # signing_key_obj = get_signing_key()
    # if not signing_key_obj:
    #     logger.error("❌ CRITICAL Error: Signing key object not available for creating ATK.")
    #     return None

    if model_id not in SUPPORTED_AI_MODELS:
        logger.warning(f"⚠️ Invalid model_id: {model_id}. Not in supported list: {SUPPORTED_AI_MODELS}. Allowing for PoC.")
        # Consider raising an error or returning None for stricter validation if desired.

    aid_subject = generate_aid(issuer_id=issuer_id_to_use, model_id=model_id, user_id=user_id)

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=expiry_minutes_to_use)

    # Validate requested permissions against the standard list (or allow custom for PoC)
    final_permissions = []
    for perm in permissions:
        perm_stripped = perm.strip()
        if not perm_stripped:
            continue
        if perm_stripped in STANDARD_PERMISSIONS_LIST:
            final_permissions.append(perm_stripped)
        else:
            logger.warning(f"⚠️ Custom permission requested: '{perm_stripped}'. Including for PoC flexibility.")
            final_permissions.append(perm_stripped) # Allow custom for PoC

    if not final_permissions:
        logger.error("❌ No valid permissions provided for ATK issuance.")
        return None

    claims = {
        "iss": issuer_id_to_use,
        "sub": aid_subject,
        "aud": audience_sp_id,
        "exp": expires_at,
        "iat": issued_at,
        "jti": str(uuid.uuid4()),
        "permissions": final_permissions, # Use the processed list
        "purpose": purpose,
    }

    # Handle actual trust tags
    current_trust_tags = {}
    if DEFAULT_AIF_TRUST_TAGS is not None:
        current_trust_tags.update(DEFAULT_AIF_TRUST_TAGS)

    if override_trust_tags:
        for key, value in override_trust_tags.items():
            if key in ALLOWED_TRUST_TAG_KEYS:
                current_trust_tags[key] = str(value).strip() # Ensure value is string and stripped
            else:
                logger.warning(f"⚠️ Unsupported override trust tag key: '{key}'. Skipping.")
    
    if current_trust_tags: # Only add the claim if there are tags
        claims["aif_trust_tags"] = current_trust_tags

    headers = {
        "alg": ALGORITHM,
        "kid": KEY_ID,
        "typ": "JWT"
    }

    try:
        signed_atk = jwt.encode(claims, private_key_pem_str, algorithm=ALGORITHM, headers=headers)
        logger.info(f"🔑 ATK issued for sub: {aid_subject}, aud: {audience_sp_id}, perms: {final_permissions}")
        return signed_atk
    except JOSEError as e:
        logger.error(f"❌ Error signing ATK with JOSE: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred during ATK signing: {e}", exc_info=True)
        return None