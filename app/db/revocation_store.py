# app/db/revocation_store.py
from datetime import datetime, timezone
from typing import Optional

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from .mongo_client import get_db
# Import collection name from settings
from config.settings import REVOKED_TOKENS_COLLECTION_NAME

def get_revoked_tokens_collection() -> Collection:
    """Returns the MongoDB collection for revoked ATKs."""
    db = get_db()
    return db[REVOKED_TOKENS_COLLECTION_NAME]

def add_jti_to_revocation_list(jti: str, original_exp_timestamp: Optional[int] = None) -> bool:
    """
    Adds a JTI to the revocation list.
    Stores the original expiry time (as Unix timestamp) for potential future cleanup.

    Args:
        jti: The JWT ID to revoke.
        original_exp_timestamp: The original 'exp' claim (Unix timestamp) of the token.

    Returns:
        True if successfully added or already exists, False on error.
    """
    if not jti:
        print("⚠️ Attempted to revoke an empty JTI.")
        return False

    collection = get_revoked_tokens_collection()
    doc_to_insert = {
        "jti": jti,
        "revoked_at": datetime.now(timezone.utc)
    }
    if original_exp_timestamp is not None:
        doc_to_insert["original_exp_ts"] = original_exp_timestamp

    try:
        # Using update_one with upsert ensures that if the JTI already exists
        # (e.g., revoked again), we just update the 'revoked_at' time.
        # It prevents duplicate JTI entries if an index enforces uniqueness on 'jti'.
        result = collection.update_one(
            {"jti": jti},
            {"$set": doc_to_insert},
            upsert=True
        )
        if result.upserted_id or result.modified_count > 0 or result.matched_count > 0:
            print(f"🛡️ JTI '{jti}' processed for revocation list.")
            return True
        else:
            # This case should ideally not happen with upsert=True unless there's a very odd race condition
            # or if the document matched but nothing changed (which is fine).
            print(f"🤔 JTI '{jti}' revocation processing had no effect (already exists identically?).")
            return True # Still consider it successful if it exists

    except PyMongoError as e:
        print(f"❌ MongoDB Error processing JTI '{jti}' for revocation: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error processing JTI '{jti}' for revocation: {e}")
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
        print("⚠️ Attempted to check revocation for an empty JTI.")
        return None

    collection = get_revoked_tokens_collection()
    try:
        document = collection.find_one({"jti": jti})
        if document:
            print(f"🛡️ JTI '{jti}' IS REVOKED (found in revocation list).")
            return True
        else:
            print(f"🛡️ JTI '{jti}' is NOT revoked (not found in revocation list).")
            return False
    except PyMongoError as e:
        print(f"❌ MongoDB Error checking JTI '{jti}': {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error checking JTI '{jti}': {e}")
        return None