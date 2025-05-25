# app/models/user_models.py
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr, HttpUrl as PydanticHttpUrl, field_validator
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# Pydantic Custom Type for MongoDB ObjectId - V2 Compatible
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema

        def validate_from_str(value: str) -> ObjectId:
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId string")
            return ObjectId(value)

        # This schema allows ObjectId instances directly or strings that are valid ObjectIds.
        # It serializes ObjectIds to strings.
        python_schema = core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId), # Allow ObjectId instance directly
                core_schema.chain_schema( # Allow string and try to convert
                    [
                        core_schema.str_schema(),
                        core_schema.no_info_plain_validator_function(validate_from_str),
                    ]
                ),
            ]
        )
        
        return core_schema.json_or_python_schema(
            python_schema=python_schema,
            json_schema=core_schema.str_schema(), # Expect a string in JSON
            serialization=core_schema.plain_serializer_function_ser_schema(str), # Serialize to string
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj, handler): # For OpenAPI schema
        json_schema = handler(core_schema_obj)
        json_schema.update(type='string', example='507f1f77bcf86cd799439011')
        return json_schema


class User(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id", description="MongoDB document ID")
    github_id: Optional[str] = Field(None, description="GitHub user ID, unique")
    github_username: Optional[str] = Field(None, description="GitHub username")
    name: Optional[str] = Field(None, description="User's full name or display name")
    email: Optional[EmailStr] = Field(None, description="Primary email address (verified if possible)")
    
    organization_name: Optional[str] = Field(None, description="Organization name (for AB/SP)")
    website: Optional[PydanticHttpUrl] = Field(None, description="Organization's website")
    
    role: Optional[str] = Field(None, description="User role, e.g., 'agent_builder', 'service_provider', 'admin'")
    
    api_token: Optional[str] = Field(None, description="Hashed API token for this user (if AB/SP)")
    api_token_generated_at: Optional[datetime] = None
    api_token_expires_at: Optional[datetime] = None
    
    registration_complete: bool = Field(False, description="Flag indicating if user has completed the onboarding process")
    
    avatar_url: Optional[PydanticHttpUrl] = Field(None, description="URL to user's avatar")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    # For Agent Builders: to store references or summaries of ATKs they've issued
    # Storing full tokens here might be too much; consider just JTIs or references.
    # For PoC, embedding a few might be okay.
    tokens_issued_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Summary of ATKs issued by this AB")

    # Pydantic V2 model configuration
    model_config = {
        "populate_by_name": True,  # Allows use of alias `_id`
        "arbitrary_types_allowed": True, 
        "json_encoders": { # How to serialize complex types to JSON
            ObjectId: str, # Fallback for ObjectId if PyObjectId isn't used everywhere
            PyObjectId: str, # PyObjectId instances to string
            datetime: lambda dt: dt.isoformat().replace("+00:00", "Z") # ISO 8601 with Z for UTC
        },
        "validate_assignment": True # Re-validate on attribute assignment
    }

    @field_validator('website', mode='before') # Pydantic v2 validator
    @classmethod
    def validate_website_format(cls, v: Optional[str]) -> Optional[str]:
        if v and isinstance(v, str) and v.strip():
            if not (v.startswith('http://') or v.startswith('https://')):
                logger.info(f"Website '{v}' missing scheme, prepending https://")
                return f'https://{v.strip()}'
            return v.strip()
        return None # Return None if input is None or empty string after stripping

# --- Other models for context, ensure they use PyObjectId if they have an _id from Mongo ---

class IssuedTokenRecord(BaseModel): # For storing in DB via token_store
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    agent_builder_id: PyObjectId # Link to the User (_id) who is the AB
    aid: str
    jti: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    audience: str
    purpose: str
    model_id: str
    permissions: List[str]
    status: str = Field("active", description="Token status (active, revoked, expired)")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, PyObjectId: str, datetime: lambda dt: dt.isoformat().replace("+00:00", "Z")}
    }

class RevokedTokenRecord(BaseModel): # For storing in DB via revocation_store
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    jti: str
    revoked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_by_user_id: Optional[PyObjectId] = None # User ID (AB) who revoked it
    original_exp_ts: Optional[int] = None # Original expiration as Unix timestamp
    # Store original_exp_dt as datetime for easier querying if needed
    original_exp_dt: Optional[datetime] = None 

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, PyObjectId: str, datetime: lambda dt: dt.isoformat().replace("+00:00", "Z")}
    }