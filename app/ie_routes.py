from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any
from datetime import datetime, timezone
import jwt
import logging
from bson import ObjectId

from app.core.token_issuer import create_atk
from app.models.atk_models import ATKIssuanceRequest, ATKIssuanceResponse
from app.models.common_models import MessageResponse
from app.auth.middleware import require_api_auth
from app.models.user_models import User  # Import the User model
from app.db.user_store import record_issued_token

router = APIRouter(
    prefix="/ie",
    tags=["Issuing Entity (IE)"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.post(
    "/issue-atk",
    response_model=ATKIssuanceResponse,
    summary="Issue a new Agent Token (ATK)",
    description="Allows authenticated Agent Builders to request an ATK "
                "for a specified user, audience, permissions, and purpose.",
    responses={
        200: {"description": "ATK issued successfully"},
        400: {"model": MessageResponse, "description": "Invalid request parameters"},
        401: {"model": MessageResponse, "description": "Authentication required"},
        500: {"model": MessageResponse, "description": "Internal server error during token issuance"},
    }
)
async def issue_new_atk(
    request_body: ATKIssuanceRequest = Body(...),
    current_user: User = Depends(require_api_auth)  # Changed from Dict[str, Any] to User
):
    """
    Issues a new Agent Token (ATK) for authenticated Agent Builders.

    - **user_id**: Identifier for the end-user delegating the agent.
    - **audience_sp_id**: The intended Service Provider audience for this token.
    - **permissions**: List of permission strings.
    - **purpose**: Description of the task this token is for.
    - **model_id**: Identifier of the AI model used.
    - **input_trust_tags**: Optional dictionary of trust tags.
    
    Requires a valid Agent Builder API token in the Authorization header.
    """
    # Fixed: Use attribute access instead of .get() method
    org_name = getattr(current_user, 'organization_name', 'Unknown Organization')
    logger.info(f"🔐 ATK issuance request from Agent Builder: {org_name}")
    logger.info(f"   User: {request_body.user_id}, Audience: {request_body.audience_sp_id}")

    # Issue the token
    signed_atk_str = create_atk(
        user_id=request_body.user_id,
        audience_sp_id=request_body.audience_sp_id,
        permissions=request_body.permissions,
        purpose=request_body.purpose,
        model_id=request_body.model_id,
        override_trust_tags=request_body.override_trust_tags
    )

    if not signed_atk_str:
        logger.error(f"❌ Failed to issue ATK for user: {request_body.user_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create and sign the Agent Token."
        )

    # Record the issued token for tracking and history
    try:
        # Decode the JWT to get the AID, JTI, and expiry
        decoded_token = jwt.decode(
            signed_atk_str, 
            options={"verify_signature": False}  # Not validating, just extracting claims
        )
        
        token_record = {
            "agent_builder_id": ObjectId(str(current_user.id)),  # Fixed: Use .id instead of ["_id"]
            "aid": decoded_token.get("sub"),
            "jti": decoded_token.get("jti"),
            "issued_at": datetime.now(timezone.utc),
            "expires_at": datetime.fromtimestamp(decoded_token.get("exp"), tz=timezone.utc),
            "audience": request_body.audience_sp_id,
            "purpose": request_body.purpose,
            "status": "active",
            "permissions": request_body.permissions,
            "model_id": request_body.model_id
        }
        
        record_id = record_issued_token(str(current_user.id), token_record)  # Fixed: Pass user_id as string
        if not record_id:
            logger.warning("⚠️ Failed to record token metadata, but token was issued successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Error recording token metadata: {e}")
        # Don't fail the request for this, just log the warning

    logger.info(f"✅ ATK issued successfully by Agent Builder: {org_name}")
    return ATKIssuanceResponse(atk=signed_atk_str)