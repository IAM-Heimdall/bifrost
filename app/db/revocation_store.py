from datetime import datetime, timezone
from typing import Optional, List, Dict
from bson import ObjectId
import logging

from .mongo_client import get_db
from .token_store import update_token_status, get_token_by_jti
from config.settings import REVOKED_TOKENS_COLLECTION_NAME

logger = logging.getLogger(__name__)

def get_revoked_tokens_collection():
    """Returns the MongoDB collection for revoked ATKs."""
    db = get_db()
    return db[REVOKED_TOKENS_COLLECTION_NAME]


def add_jti_to_revocation_list(
    jti: str, 
    original_exp_timestamp: Optional[int] = None,
    agent_builder_id: Optional[str] = None
) -> bool:
    """
    Adds a JTI to the revocation list.
    Stores the original expiry time (as Unix timestamp) for potential future cleanup.

    Args:
        jti: The JWT ID to revoke.
        original_exp_timestamp: The original 'exp' claim (Unix timestamp) of the token.
        agent_builder_id: The ID of the agent builder revoking the token (if authenticated)

    Returns:
        True if successfully added or already exists, False on error.
    """
    if not jti:
        logger.warning("⚠️ Attempted to revoke an empty JTI.")
        return False

    try:
        collection = get_revoked_tokens_collection()
        
        doc_to_insert = {
            "jti": jti,
            "revoked_at": datetime.now(timezone.utc)
        }
        
        if original_exp_timestamp is not None:
            doc_to_insert["original_exp_ts"] = original_exp_timestamp
            
        if agent_builder_id:
            doc_to_insert["revoked_by"] = ObjectId(agent_builder_id)

        # Using update_one with upsert ensures that if the JTI already exists
        # (e.g., revoked again), we just update the 'revoked_at' time.
        result = collection.update_one(
            {"jti": jti},
            {"$set": doc_to_insert},
            upsert=True
        )
        
        # If this token is in our issued_tokens collection, update its status
        update_token_status(jti, "revoked")
        
        if result.upserted_id or result.modified_count > 0 or result.matched_count > 0:
            logger.info(f"🛡️ JTI '{jti}' processed for revocation list by user {agent_builder_id}")
            return True
        else:
            logger.warning(f"🤔 JTI '{jti}' revocation processing had no effect (already exists identically?).")
            return True  # Still consider it successful
    except Exception as e:
        logger.error(f"❌ Error processing JTI '{jti}' for revocation: {e}")
        return False

def is_jti_revoked(jti: str) -> Optional[bool]:
    """
    Checks if a JTI is in the revocation list.

    Args:
        jti: The JWT ID to check.

    Returns:
        True if revoked, False if not revoked.
        None if there was an error during the check.
    """
    if not jti:
        logger.warning("⚠️ Attempted to check revocation for an empty JTI.")
        return None

    try:
        collection = get_revoked_tokens_collection()
        document = collection.find_one({"jti": jti})
        
        if document:
            logger.info(f"🛡️ JTI '{jti}' IS REVOKED (found in revocation list).")
            return True
        else:
            logger.info(f"🛡️ JTI '{jti}' is NOT revoked (not found in revocation list).")
            return False
    except Exception as e:
        logger.error(f"❌ Error checking JTI '{jti}': {e}")
        return None

def get_revoked_tokens(agent_builder_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Get list of revoked tokens, optionally filtered by agent builder.
    
    Args:
        agent_builder_id: If provided, only return tokens revoked by this agent builder
        limit: Maximum number of tokens to return (default 20)
        
    Returns:
        List of revoked token records
    """
    try:
        collection = get_revoked_tokens_collection()
        query = {}
        
        if agent_builder_id:
            query["revoked_by"] = ObjectId(agent_builder_id)
        
        tokens = list(
            collection.find(
                query, 
                {"_id": 0, "jti": 1, "revoked_at": 1, "original_exp_ts": 1, "revoked_by": 1}
            ).sort("revoked_at", -1).limit(limit)
        )
        
        # For each token, try to get more info from issued_tokens collection
        for token in tokens:
            jti = token.get("jti")
            if jti:
                token_info = get_token_by_jti(jti)
                if token_info:
                    token["aid"] = token_info.get("aid")
                    token["audience"] = token_info.get("audience")
                    token["purpose"] = token_info.get("purpose")
        
        return tokens
    except Exception as e:
        logger.error(f"❌ Error retrieving revoked tokens: {e}")
        return []


def can_user_revoke_token(user_id: str, jti: str) -> Optional[bool]:
    """
    Check if a user can revoke a specific token (i.e., they issued it).
    
    Args:
        user_id: The ID of the user attempting to revoke the token
        jti: The JWT ID of the token to check
        
    Returns:
        True if user can revoke the token
        False if user cannot revoke the token  
        None if there was an error during the check
    """
    if not user_id or not jti:
        logger.warning("⚠️ Missing user_id or jti in can_user_revoke_token")
        return None
    
    try:
        # Get token information from issued_tokens collection
        token_info = get_token_by_jti(jti)
        
        if not token_info:
            logger.info(f"🔍 Token with JTI '{jti}' not found in issued tokens")
            return False
        
        # Check if the token was issued by this user
        token_issuer_id = token_info.get("agent_builder_id")
        
        if not token_issuer_id:
            logger.warning(f"⚠️ Token '{jti}' has no agent_builder_id recorded")
            return False
        
        # Convert to string for comparison (handle ObjectId)
        if isinstance(token_issuer_id, ObjectId):
            token_issuer_id = str(token_issuer_id)
        
        user_can_revoke = str(token_issuer_id) == str(user_id)
        
        logger.info(f"🔍 Ownership check for JTI '{jti}': "
                   f"Issuer={token_issuer_id}, Requester={user_id}, "
                   f"CanRevoke={user_can_revoke}")
        
        return user_can_revoke
        
    except Exception as e:
        logger.error(f"❌ Error checking token ownership for JTI '{jti}': {e}")
        return None


