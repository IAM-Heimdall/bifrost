from fastapi import APIRouter, Request, Form, HTTPException # Removed Depends for now
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Dict, Optional
import logging
import json
from datetime import datetime, timezone

# Core imports
from .core.token_issuer import create_atk
from .db.revocation_store import add_jti_to_revocation_list, get_revoked_tokens_collection
from .core.key_manager import get_jwks

# Import configurations from settings.py
from config.settings import (
    CORE_AIF_SERVICE_ISSUER_ID,
    SUPPORTED_AI_MODELS,
    STANDARD_PERMISSIONS_LIST,
    DEFAULT_AIF_TRUST_TAGS, # Used to display info, and by token_issuer
    # ALLOWED_TRUST_TAG_KEYS # No longer directly needed by UI form for overrides
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
if not TEMPLATES_DIR.is_dir():
    logging.critical(f"CRITICAL: Templates directory not found at {TEMPLATES_DIR}.")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(
    prefix="/ui",
    tags=["UI (PoC Management)"],
    default_response_class=HTMLResponse
)

def get_base_template_context(request: Request, title: str) -> Dict:
    return {"request": request, "title": title, "user_name": "Admin User (PoC)", "user_initials": "AD"}

@router.get("/", response_class=HTMLResponse)
async def ui_dashboard(request: Request):
    context = get_base_template_context(request, "AIF Core Service - PoC Dashboard")
    try:
        jwks_data = get_jwks()
        jwks_url_path = "/.well-known/jwks.json" # Default if url_for fails
        try:
            jwks_url_path = request.app.url_path_for('get_jwks_endpoint')
        except Exception as url_err:
            logging.warning(f"Could not generate URL for 'get_jwks_endpoint': {url_err}. Using fallback.")
        
        context.update({
            "jwks_url": jwks_url_path,
            "jwks_content_str": json.dumps(jwks_data, indent=2) if jwks_data else "JWKS Not Available",
            "issuer_id": CORE_AIF_SERVICE_ISSUER_ID
        })
        return templates.TemplateResponse("index.html", context)
    except Exception as e:
        logging.error(f"Error rendering UI dashboard: {e}", exc_info=True)
        error_context = get_base_template_context(request, "Error")
        error_context["error_message"] = f"Could not load dashboard: {e}"
        return templates.TemplateResponse("error_page.html", error_context, status_code=500)

@router.get("/issue-token", response_class=HTMLResponse)
async def issue_token_form_get(request: Request):
    context = get_base_template_context(request, "Issue New ATK (Manual PoC)")
    context.update({
        "supported_models": SUPPORTED_AI_MODELS,
        "standard_permissions": STANDARD_PERMISSIONS_LIST,
        "default_trust_tags_info": DEFAULT_AIF_TRUST_TAGS if DEFAULT_AIF_TRUST_TAGS is not None else {}, # Pass dict or empty
        "form_data": {} 
    })
    return templates.TemplateResponse("issue_token_ui.html", context)

@router.post("/issue-token", response_class=HTMLResponse)
async def issue_token_form_post(
    request: Request,
    user_id: str = Form(..., min_length=1),
    audience_sp_id: str = Form(..., min_length=1),
    input_permissions_str: str = Form(..., alias="permissions", min_length=1),
    purpose: str = Form(..., min_length=1),
    model_id: str = Form(...)
    # Removed override_trust_tag_keys, override_trust_tag_values, override_trust_tags_json_str
):
    context = get_base_template_context(request, "Issue New ATK (Manual PoC)")
    form_data_repopulate = {
        "user_id": user_id, "audience_sp_id": audience_sp_id,
        "permissions_str": input_permissions_str, "purpose": purpose,
        "model_id": model_id
    }
    message = ""
    message_type = "error"
    issued_atk_val = None

    try:
        if not all([user_id, audience_sp_id, input_permissions_str, purpose, model_id]): # Basic check
            raise ValueError("All fields are required.")

        actual_permissions = [p.strip() for p in input_permissions_str.split(',') if p.strip()]
        if not actual_permissions:
            raise ValueError("At least one permission is required.")

        # For PoC Phase 1, override_trust_tags will be None,
        # so create_atk will use DEFAULT_AIF_TRUST_TAGS from settings.
        signed_atk = create_atk(
            user_id=user_id.strip(),
            audience_sp_id=audience_sp_id.strip(),
            permissions=actual_permissions,
            purpose=purpose.strip(),
            model_id=model_id.strip(),
            override_trust_tags=None # Explicitly pass None for overrides from UI
        )
        
        if signed_atk:
            message = "✅ ATK issued successfully!"
            if DEFAULT_AIF_TRUST_TAGS:
                message += f" (Default trust tags applied: {json.dumps(DEFAULT_AIF_TRUST_TAGS)})"
            else:
                message += " (No default trust tags configured to be applied.)"
            message_type = "success"
            issued_atk_val = signed_atk
            form_data_repopulate = {"model_id": model_id} # Clear for next, keep model
        else:
            message = "❌ Failed to issue ATK. Check server logs."
        
    except ValueError as e:
        message = f"❌ Validation error: {str(e)}"
    except Exception as e:
        logging.error(f"Error issuing token via UI: {e}", exc_info=True)
        message = "❌ Unexpected error occurred. Check server logs."

    context.update({
        "message": message,
        "message_type": message_type,
        "issued_atk": issued_atk_val,
        "supported_models": SUPPORTED_AI_MODELS,
        "standard_permissions": STANDARD_PERMISSIONS_LIST,
        "default_trust_tags_info": DEFAULT_AIF_TRUST_TAGS if DEFAULT_AIF_TRUST_TAGS is not None else {},
        "form_data": form_data_repopulate
    })
    return templates.TemplateResponse("issue_token_ui.html", context)

@router.get("/revoke-token", response_class=HTMLResponse)
async def revoke_token_form_get(request: Request, message: Optional[str] = None, msg_type: Optional[str] = "info"):
    """Displays a form to manually revoke an ATK by JTI, and shows message if redirected."""
    context = get_base_template_context(request, "Revoke ATK (Manual PoC)")
    current_revoked_jtis_processed = []
    try:
        revoked_collection = get_revoked_tokens_collection()
        current_revoked_jtis_raw = list(
            revoked_collection.find({}, {"_id": 0, "jti": 1, "revoked_at": 1, "original_exp_ts": 1})
            .sort("revoked_at", -1).limit(20)
        )
        for item_raw in current_revoked_jtis_raw:
            item = dict(item_raw)
            if item.get("original_exp_ts") and isinstance(item["original_exp_ts"], (int, float)):
                try:
                    item["original_exp_ts_dt"] = datetime.fromtimestamp(item["original_exp_ts"], tz=timezone.utc)
                except Exception: # Handle potential errors if timestamp is out of range or invalid
                    item["original_exp_ts_dt"] = "Invalid Timestamp"
            else:
                item["original_exp_ts_dt"] = None # Or "N/A"
            current_revoked_jtis_processed.append(item)

    except Exception as e:
        logging.error(f"Error fetching revoked tokens for UI: {e}", exc_info=True)
        if not message: # Don't overwrite redirect message
            message = "Error fetching current revocation list from database."
            msg_type = "error"
    
    context.update({
        "current_revoked_jtis": current_revoked_jtis_processed,
        "message": message,
        "message_type": msg_type
    })
    return templates.TemplateResponse("revoke_token_ui.html", context)


@router.post("/revoke-token")
async def revoke_token_form_post(request: Request, jti: str = Form(..., min_length=1)):
    """Handles ATK revocation from the UI form and redirects back."""
    message = ""
    msg_type = "error"
    try:
        if not jti.strip(): # Should be caught by FastAPI Form validation
            raise ValueError("JTI value cannot be empty.")
        
        # Get original_exp_ts if needed - for PoC, this is optional.
        # If you wanted to log the original expiry of the token being revoked, you'd
        # need a way to fetch the token details by JTI before adding to revocation list,
        # which is complex as ATKs are not typically stored by the IE after issuance.
        # For now, we pass None for original_exp_timestamp.
        success = add_jti_to_revocation_list(jti=jti.strip(), original_exp_timestamp=None)
        
        if success:
            message = f"✅ JTI '{jti}' successfully processed for revocation."
            msg_type = "success"
        else:
            message = f"❌ Failed to add JTI '{jti}' to revocation list. It might already be there or a DB error occurred."
            
    except ValueError as e: # Catch specific validation errors
        message = f"❌ Validation Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error revoking token via UI for JTI '{jti}': {e}", exc_info=True)
        message = f"❌ Unexpected error revoking JTI '{jti}'. Check server logs."
    
    redirect_url = request.url_for("revoke_token_form_get").include_query_params(message=message, msg_type=msg_type)
    return RedirectResponse(url=str(redirect_url), status_code=303)


# --- Phase 2 Placeholder Routes ---
@router.get("/register/agent-builder", response_class=HTMLResponse)
async def register_agent_builder_form_get(request: Request):
    context = get_base_template_context(request, "Register as Agent Builder (Phase 2 Placeholder)")
    return templates.TemplateResponse("registration_ab.html", context)

@router.post("/register/agent-builder", response_class=HTMLResponse)
async def register_agent_builder_form_post(request: Request):
    context = get_base_template_context(request, "Register as Agent Builder (Phase 2 Placeholder)")
    context["message"] = "Agent Builder registration functionality will be implemented in Phase 2."
    context["message_type"] = "info"
    return templates.TemplateResponse("registration_ab.html", context)

@router.get("/register/service-provider", response_class=HTMLResponse)
async def register_service_provider_form_get(request: Request):
    context = get_base_template_context(request, "Register as Service Provider (Phase 2 Placeholder)")
    return templates.TemplateResponse("registration_sp.html", context)

@router.post("/register/service-provider", response_class=HTMLResponse)
async def register_service_provider_form_post(request: Request):
    context = get_base_template_context(request, "Register as Service Provider (Phase 2 Placeholder)")
    context["message"] = "Service Provider registration functionality will be implemented in Phase 2."
    context["message_type"] = "info"
    return templates.TemplateResponse("registration_sp.html", context)

# Simple Error Page Template (Create `app/templates/error_page.html`)
# This is a fallback if specific error handling in routes doesn't catch something for UI.
# @router.exception_handler(Exception)
# async def generic_ui_exception_handler(request: Request, exc: Exception):
#     logging.error(f"Unhandled exception in UI route: {exc}", exc_info=True)
#     context = get_base_template_context(request, "Error")
#     context["error_message"] = "An unexpected error occurred in the UI."
#     return templates.TemplateResponse("error_page.html", context, status_code=500)