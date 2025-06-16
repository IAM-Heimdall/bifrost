# app/reg_routes.py
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Dict, Any

from app.core.key_manager import get_jwks
from app.auth.middleware import require_api_auth  
from app.models.user_models import User 
from app.db.revocation_store import add_jti_to_revocation_list, is_jti_revoked, can_user_revoke_token 
from app.models.atk_models import JWKS, ATKRevocationRequest, RevocationStatusResponse
from app.models.common_models import MessageResponse
from datetime import datetime, timezone # For RevocationStatusResponse default

router = APIRouter(
    tags=["Registry (REG)"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/.well-known/jwks.json",
    response_model=JWKS, # Use the Pydantic model for response schema
    summary="Get JSON Web Key Set (JWKS)",
    description="Provides the public keys of this Issuing Entity (acting as REG for itself in PoC) "
                "for verifying ATK signatures.",
    responses={
        200: {"description": "JWKS retrieved successfully"},
        500: {"model": MessageResponse, "description": "Internal server error if keys cannot be loaded"},
    }
)
async def get_jwks_endpoint():
    """
    Serves the JSON Web Key Set (JWKS) containing the public key(s)
    used by this AIF Core Service (acting as IE) to sign ATKs.
    """
    jwks_data = get_jwks() # From key_manager
    if not jwks_data or not jwks_data.get("keys"):
        print("❌ JWKS data is not available or keys are missing.")
        raise HTTPException(status_code=500, detail="Key material not available.")
    return JWKS(**jwks_data) # Validate against Pydantic model before returning

@router.post(
    "/reg/revoke-atk",
    response_model=MessageResponse,
    summary="Revoke an Agent Token (ATK) by its JTI",
    description="Adds a JTI to the revocation list. Requires authentication and only allows "
                "revoking tokens issued by the authenticated user.",
    responses={
        200: {"description": "JTI successfully added to revocation list"},
        400: {"model": MessageResponse, "description": "Invalid request (e.g., missing JTI)"},
        401: {"model": MessageResponse, "description": "Authentication required"},
        403: {"model": MessageResponse, "description": "Not authorized to revoke this token"},
        404: {"model": MessageResponse, "description": "Token not found or not issued by user"},
        500: {"model": MessageResponse, "description": "Internal server error"},
    }
)
async def revoke_atk_endpoint(
    request_body: ATKRevocationRequest = Body(...),
    current_user: User = Depends(require_api_auth)  # ADD AUTHENTICATION DEPENDENCY
):
    """
    Revokes an ATK by adding its JTI to the blacklist.
    Only the original issuer (Agent Builder) can revoke their tokens.
    
    - **jti**: The JWT ID of the token to revoke.
    """
    jti = request_body.jti.strip()
    user_id = str(current_user.id)
    
    print(f"🔐 Revocation request for JTI: {jti} by user: {user_id}")
    
    # Validate that the user can revoke this token
    can_revoke = can_user_revoke_token(user_id, jti)
    
    if can_revoke is None:
        print(f"❌ Error checking revocation permissions for JTI: {jti}")
        raise HTTPException(
            status_code=500, 
            detail="Error validating token ownership"
        )
    
    if not can_revoke:
        print(f"🚫 User {user_id} attempted to revoke token {jti} they don't own")
        raise HTTPException(
            status_code=403, 
            detail="You can only revoke tokens that you have issued"
        )
    
    # Proceed with revocation
    success = add_jti_to_revocation_list(
        jti=jti,
        agent_builder_id=user_id
    )
    
    if not success:
        print(f"❌ Failed to add JTI '{jti}' to revocation list")
        raise HTTPException(
            status_code=500, 
            detail="Failed to add JTI to revocation list"
        )
    
    print(f"✅ JTI '{jti}' successfully revoked by user {user_id}")
    return MessageResponse(
        message=f"Token '{jti}' successfully revoked"
    )

@router.get(
    "/reg/revocation-status",
    response_model=RevocationStatusResponse,
    summary="Check if an ATK JTI is revoked",
    description="Queries the revocation status of a given JTI. This endpoint would be called by SPs.",
    responses={
        200: {"description": "Revocation status retrieved"},
        400: {"model": MessageResponse, "description": "Invalid request (e.g., missing JTI)"},
        500: {"model": MessageResponse, "description": "Internal server error during lookup"},
    }
)
async def get_revocation_status_endpoint(
    jti: str = Query(..., description="The JWT ID (jti claim) to check for revocation.")
):
    """
    Checks if a given JTI has been revoked.
    - **jti**: The JTI to check.
    """
    print(f"Received revocation status check for JTI: {jti}")
    if not jti: # Should be caught by FastAPI's Query(...) if jti is required
        raise HTTPException(status_code=400, detail="JTI query parameter is required.")

    revoked_status = is_jti_revoked(jti=jti)

    if revoked_status is None: # Indicates an error during DB lookup
        print(f"❌ Error checking revocation status for JTI: {jti}")
        raise HTTPException(status_code=500, detail="Error checking token revocation status.")
    
    print(f"✅ Revocation status for JTI '{jti}': {revoked_status}")
    return RevocationStatusResponse(
        jti=jti,
        is_revoked=revoked_status,
        # checked_at is defaulted by Pydantic model
    )

# Add other REG-specific routes here in the future (e.g., for SP registration info, issuer lists if federated)