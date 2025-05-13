# app/reg_routes.py
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Dict, Any

from app.core.key_manager import get_jwks
from app.db.revocation_store import add_jti_to_revocation_list, is_jti_revoked
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


# For PoC, /revoke-atk is simple. In production, it would need strong auth.
# For example, only the user who delegated, the IE that issued, or an admin should revoke.
# async def verify_revocation_authority(jti_to_revoke: str, current_user: User = Depends(get_current_user)):
#     # Logic to check if current_user is authorized to revoke token with jti_to_revoke
#     pass

@router.post(
    "/reg/revoke-atk",
    response_model=MessageResponse,
    summary="Revoke an Agent Token (ATK) by its JTI",
    description="Adds a JTI to the revocation list. For PoC, this endpoint is open. "
                "In production, it MUST be authenticated and authorized.",
    responses={
        200: {"description": "JTI successfully added to revocation list"},
        400: {"model": MessageResponse, "description": "Invalid request (e.g., missing JTI)"},
        500: {"model": MessageResponse, "description": "Internal server error"},
    }
)
async def revoke_atk_endpoint(
    request_body: ATKRevocationRequest = Body(...)
    # authorized_revoker: bool = Depends(verify_revocation_authority) # Example for future
):
    """
    Revokes an ATK by adding its JTI to the blacklist.
    - **jti**: The JWT ID of the token to revoke.
    """
    print(f"Received request to revoke JTI: {request_body.jti}")
    # In a real app, you might want to get the `exp` of the token being revoked
    # to store it alongside the jti for easier cleanup of old revoked tokens.
    # For PoC, just storing jti is fine. `original_exp_timestamp` in `add_jti_to_revocation_list` supports this.
    success = add_jti_to_revocation_list(jti=request_body.jti)
    if not success:
        print(f"❌ Failed to add JTI '{request_body.jti}' to revocation list.")
        raise HTTPException(status_code=500, detail="Failed to add JTI to revocation list.")
    
    print(f"✅ JTI '{request_body.jti}' added to revocation list.")
    return MessageResponse(message=f"JTI '{request_body.jti}' successfully added to revocation list.")


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