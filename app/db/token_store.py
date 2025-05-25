# app/db/token_store.py
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging

from .mongo_client import get_db

logger = logging.getLogger(__name__)

# Collection name
ISSUED_TOKENS_COLLECTION = "issued_tokens"

def get_issued_tokens_collection():
    """Get the issued tokens collection."""
    db = get_db()
    return db[ISSUED_TOKENS_COLLECTION]

def update_token_status(jti: str, status: str) -> bool:
    """Update the status of a token (active, expired, revoked)."""
    try:
        collection = get_issued_tokens_collection()
        
        result = collection.update_one(
            {"jti": jti},
            {"$set": {"status": status}}
        )
        
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating token status: {e}")
        return False

def get_token_by_jti(jti: str) -> Optional[dict]:
    """Get a token by its JTI."""
    try:
        collection = get_issued_tokens_collection()
        return collection.find_one({"jti": jti})
    except Exception as e:
        logger.error(f"Error retrieving token by JTI: {e}")
        return None

def add_issued_token_record(user_id: str, token_record: dict) -> bool:
    """Add a record of an issued token to the user's history."""
    try:
        # Add agent_builder_id if not in record
        if "agent_builder_id" not in token_record:
            token_record["agent_builder_id"] = ObjectId(user_id)
        
        # Add timestamp if not in record
        if "issued_at" not in token_record:
            token_record["issued_at"] = datetime.now(timezone.utc)
        
        # Store the token record
        collection = get_issued_tokens_collection()
        result = collection.insert_one(token_record)
        
        # Also add to user's tokens_issued array
        from .user_store import get_users_collection  # Import here to avoid circular import
        users_collection = get_users_collection()
        update_result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"tokens_issued": token_record}}
        )
        
        return result.inserted_id is not None
    except Exception as e:
        logger.error(f"Error adding token record: {e}")
        return False

def get_user_issued_tokens(user_id: str, status: Optional[str] = None, limit: int = 20) -> List[dict]:
    """Get tokens issued by a specific user with optional status filter."""
    try:
        collection = get_issued_tokens_collection()
        
        query = {"agent_builder_id": ObjectId(user_id)}
        if status:
            query["status"] = status
        
        tokens = list(collection.find(query).sort("issued_at", -1).limit(limit))
        
        # Convert ObjectId to string
        for token in tokens:
            if "_id" in token:
                token["_id"] = str(token["_id"])
            if "agent_builder_id" in token:
                token["agent_builder_id"] = str(token["agent_builder_id"])
        
        return tokens
    except Exception as e:
        logger.error(f"Error retrieving user issued tokens: {e}")
        return []