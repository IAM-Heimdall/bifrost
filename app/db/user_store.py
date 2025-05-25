# app/db/user_store.py
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging

from .mongo_client import get_db
from app.auth.token_utils import generate_api_token
# Import from token_store
from .token_store import (
    get_issued_tokens_collection,  # For backwards compatibility
    get_token_by_jti,
    update_token_status,
    add_issued_token_record,
    get_user_issued_tokens
)

record_issued_token = add_issued_token_record # Alias for backward compatibility

logger = logging.getLogger(__name__)

# Collection names
USERS_COLLECTION = "users"

def get_users_collection():
    """Get the users collection."""
    db = get_db()
    return db[USERS_COLLECTION]

def get_user_by_github_id(github_id: str) -> Optional[dict]:
    """Get a user by GitHub ID."""
    try:
        collection = get_users_collection()
        return collection.find_one({"github_id": github_id})
    except Exception as e:
        logger.error(f"Error retrieving user by GitHub ID: {e}")
        return None

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get a user by internal ID."""
    try:
        collection = get_users_collection()
        return collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        logger.error(f"Error retrieving user by ID: {e}")
        return None

def complete_user_registration(user_id: str, registration_data: dict) -> Optional[dict]:
    """Complete user registration with organization details."""
    try:
        collection = get_users_collection()
        
        # Generate API token
        api_token, expires_at = generate_api_token(user_id)
        
        # Update user with registration data
        update_data = {
            "organization_name": registration_data.get("organization_name"),
            "website": registration_data.get("website"),
            "registration_complete": True,
            "api_token": api_token,
            "api_token_generated_at": datetime.now(timezone.utc),
            "api_token_expires_at": expires_at,
            "role": "agent_builder",  # Default role for now
            "tokens_issued": []  # Initialize empty array for token history
        }
        
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return collection.find_one({"_id": ObjectId(user_id)})
        return None
    except Exception as e:
        logger.error(f"Error completing user registration: {e}")
        return None

def regenerate_api_token(user_id: str) -> Optional[dict]:
    """Generate a new API token for a user."""
    try:
        collection = get_users_collection()
        
        # Generate new token
        api_token, expires_at = generate_api_token(user_id)
        
        # Update user with new token
        update_data = {
            "api_token": api_token,
            "api_token_generated_at": datetime.now(timezone.utc),
            "api_token_expires_at": expires_at
        }
        
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return collection.find_one({"_id": ObjectId(user_id)})
        return None
    except Exception as e:
        logger.error(f"Error regenerating API token: {e}")
        return None

def get_agent_builder_by_user_id(user_id: str) -> Optional[dict]:
    """Get Agent Builder profile by user ID."""
    try:
        # For now, Agent Builder profile is just the user record
        # with role = "agent_builder"
        user = get_user_by_id(user_id)
        if user and user.get("role") == "agent_builder":
            # Add tokens_issued if missing
            if "tokens_issued" not in user:
                user["tokens_issued"] = []
            return user
        return None
    except Exception as e:
        logger.error(f"Error retrieving Agent Builder profile: {e}")
        return None

def get_service_provider_by_user_id(user_id: str) -> Optional[dict]:
    """Get Service Provider profile by user ID."""
    try:
        # For now, Service Provider profile is just the user record
        # with role = "service_provider"
        user = get_user_by_id(user_id)
        if user and user.get("role") == "service_provider":
            # Add validation_requests if missing
            if "validation_requests" not in user:
                user["validation_requests"] = []
            # Add audience_ids if missing  
            if "audience_ids" not in user:
                user["audience_ids"] = []
            return user
        return None
    except Exception as e:
        logger.error(f"Error retrieving Service Provider profile: {e}")
        return None