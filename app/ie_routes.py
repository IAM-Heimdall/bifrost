# app/ie_routes.py
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any

from app.core.token_issuer import create_atk
from app.models.atk_models import ATKIssuanceRequest, ATKIssuanceResponse
from app.models.common_models import MessageResponse # For error responses
# from config.settings import SUPPORTED_AI_MODELS # Already used in token_issuer

# In a real app with AB authentication, you'd have a dependency for that.
# For PoC, we might not have specific AB auth for this endpoint.
# async def verify_agent_builder_auth(api_key: str = Security(api_key_header)):
#     if api_key != "POC_AB_SHARED_SECRET": # Simplistic PoC auth
#         raise HTTPException(status_code=401, detail="Invalid Agent Builder API Key")
#     return True

router = APIRouter(
    prefix="/ie",  # Prefix for Issuing Entity specific routes
    tags=["Issuing Entity (IE)"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/issue-atk",
    response_model=ATKIssuanceResponse,
    summary="Issue a new Agent Token (ATK)",
    description="Allows a trusted Agent Builder (implicitly trusted in PoC) to request an ATK "
                "for a specified user, audience, permissions, and purpose.",
    responses={
        200: {"description": "ATK issued successfully"},
        400: {"model": MessageResponse, "description": "Invalid request parameters"},
        500: {"model": MessageResponse, "description": "Internal server error during token issuance"},
    }
)
async def issue_new_atk(
    request_body: ATKIssuanceRequest = Body(...)
    # For PoC, we don't authenticate the Agent Builder calling this.
    # In production, this endpoint would be protected.
    # authorized: bool = Depends(verify_agent_builder_auth) # Example of future auth
):
    """
    Issues a new Agent Token (ATK).

    - **user_id**: Identifier for the end-user delegating the agent.
    - **audience_sp_id**: The intended Service Provider audience for this token.
    - **permissions**: List of permission strings.
    - **purpose**: Description of the task this token is for.
    - **model_id**: Identifier of the AI model used.
    - **input_trust_tags**: Optional dictionary of trust tags.
    """
    print(f"Received ATK issuance request for user: {request_body.user_id}, audience: {request_body.audience_sp_id}")

    # In token_issuer.py, CORE_AIF_SERVICE_ISSUER_ID is used by default.
    # Model ID validation also happens within create_atk based on settings.
    # Trust tag validation also happens within create_atk.
    signed_atk_str = create_atk(
        user_id=request_body.user_id,
        audience_sp_id=request_body.audience_sp_id,
        permissions=request_body.permissions,
        purpose=request_body.purpose,
        model_id=request_body.model_id,
        override_trust_tags=request_body.override_trust_tags
        # expiry_minutes can be taken from settings or made a request param
    )

    if not signed_atk_str:
        print(f"❌ Failed to issue ATK for user: {request_body.user_id}, audience: {request_body.audience_sp_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create and sign the Agent Token."
        )

    print(f"✅ ATK issued successfully for user: {request_body.user_id}")
    return ATKIssuanceResponse(atk=signed_atk_str)

# Add other IE-specific routes here in the future if needed