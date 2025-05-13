# app/models/atk_models.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone # Ensure datetime class is imported
from pydantic import BaseModel, Field, validator

class ATKIssuanceRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User identifier for delegation.", example="user-poc-001")
    audience_sp_id: str = Field(..., min_length=1, description="Target Service Provider audience.", example="https://sp.example.com/api")
    permissions: List[str] = Field(..., min_length=1, description="Specific permissions granted.", example=["read:articles_all", "summarize:text_content_short"])
    purpose: str = Field(..., min_length=1, description="Purpose of this token/agent task.", example="Fetch and summarize tech news.")
    model_id: str = Field(..., description="AI model identifier used.", example="general-text-v1")
    # This is for providing *actual* trust tags, not permissions.
    # For PoC, this can be kept simple or use the default from settings.
    override_trust_tags: Optional[Dict[str, str]] = Field(None, description="Optional key-value pairs for trust metadata, overriding defaults if specified.", example={"user_verification_level": "simulated_user_poc"})

    @validator('audience_sp_id')
    def audience_must_be_valid_identifier(cls, v):
        if not v.strip() or " " in v: # Keep simple validation for PoC
            raise ValueError('Audience SP ID must be a non-empty string without spaces.')
        return v.strip()

    @validator('permissions', each_item=True)
    def permission_string_format(cls, v):
        if not v.strip() or ":" not in v: # Basic check for "action:resource" like format
            # raise ValueError(f"Permission '{v}' should be in 'action:resource' format.")
            # For PoC, be lenient, but good to note.
            pass
        return v.strip()

class ATKIssuanceResponse(BaseModel):
    atk: str = Field(..., description="The signed Agent Token (ATK) as a JWT string.")

class ATKRevocationRequest(BaseModel):
    jti: str = Field(..., min_length=1, description="The JWT ID (jti claim) of the ATK to be revoked.")

class RevocationStatusResponse(BaseModel):
    jti: str
    is_revoked: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True} # Kept for safety with datetime

class JWK(BaseModel):
    kty: str = Field("OKP")
    crv: str = Field("Ed25519")
    kid: str
    x: str
    alg: str = Field("EdDSA")
    use: str = Field("sig")

class JWKS(BaseModel):
    keys: List[JWK]