# app/ui_routes.py
from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Dict, Optional
import logging
import json
from datetime import datetime, timezone
import jwt # For decoding ATK to get JTI in issue_token_form_post

from app.utils.docs import render_markdown_file

# Core imports
from .core.token_issuer import create_atk
# Updated to use get_revoked_tokens for the revoke_token_form_get display
from .db.revocation_store import add_jti_to_revocation_list, get_revoked_tokens, is_jti_revoked
from .core.key_manager import get_jwks
from .models.user_models import User # Assuming User model is Pydantic or similar
from .auth.middleware import (
    get_optional_current_user,
    require_authenticated_user,
    require_agent_builder,
    # require_service_provider # Not used yet in UI routes but good for future
)
from .db.user_store import (
    get_agent_builder_by_user_id,
    regenerate_api_token,
    # get_service_provider_by_user_id,
)
from .db.token_store import add_issued_token_record, get_user_issued_tokens

# Import configurations
from config.settings import (
    CORE_AIF_SERVICE_ISSUER_ID,
    SUPPORTED_AI_MODELS,
    STANDARD_PERMISSIONS_LIST,
    DEFAULT_AIF_TRUST_TAGS,
    BASE_URL, # For templates that might need it
    # ALLOWED_TRUST_TAG_KEYS # Only if we re-introduce UI override for trust tags
)

# Initialize Logging
logger = logging.getLogger(__name__)

# Initialize Templates
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
if not TEMPLATES_DIR.is_dir():
    logging.critical(f"CRITICAL: Templates directory not found at {TEMPLATES_DIR}. UI will not work.")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(
    prefix="/ui",
    tags=["UI (Application & Management)"],
    default_response_class=HTMLResponse
)

# --- Helper for common template context ---
def get_base_template_context(request: Request, title: str, current_user: Optional[User] = None) -> Dict:
    active_section = ""
    path = str(request.url.path) # Convert to string for endswith/in checks
    
    # Use request.app.url_path_for to get the path for named routes
    try:
        if path == request.app.url_path_for("ui_dashboard_dispatch"): active_section = "dashboard"
        elif path == request.app.url_path_for("verify_agents_public"): active_section = "verify-agents" 
        elif path == request.app.url_path_for("issue_token_form_get"): active_section = "issue-token"
        elif path == request.app.url_path_for("revoke_token_form_get"): active_section = "revoke-token"
        elif path == request.app.url_path_for("revoked_tokens_check_form"): active_section = "revoked-tokens"
        elif path == request.app.url_path_for("documentation_page"): active_section = "documentation"
        elif path == request.app.url_path_for("profile_page"): active_section = "profile"
        elif path == request.app.url_path_for("start_here_page"): active_section = "start-here"
        # READ section routes - MOVED TO CORRECT LOCATION
        elif path == request.app.url_path_for("api_reference_page"): active_section = "api-reference"
        elif path == request.app.url_path_for("whitepaper_page"): active_section = "whitepaper"
        elif path == request.app.url_path_for("sdk_agent_builder_page"): active_section = "sdk-ab"
        elif path == request.app.url_path_for("sdk_service_provider_page"): active_section = "sdk-sp"
        
    except Exception as e:
        logger.warning(f"Could not determine active section due to url_for error: {e}")
        # Fallback based on raw path
        if path.endswith("/dashboard"): active_section = "dashboard"
        elif "/verify" in path: active_section = "verify-agents"
        elif "/issue-token" in path: active_section = "issue-token"
        elif "/revoke-token" in path: active_section = "revoke-token"
        elif "/revoked-tokens" in path: active_section = "revoked-tokens"
        elif "/documentation" in path: active_section = "documentation"
        elif "/profile" in path: active_section = "profile"
        elif "/start-here" in path: active_section = "start-here"
        # READ section fallbacks
        elif "/api-reference" in path: active_section = "api-reference"
        elif "/whitepaper" in path: active_section = "whitepaper"
        elif "/sdk/agent-builder" in path: active_section = "sdk-ab"
        elif "/sdk/service-providers" in path: active_section = "sdk-sp"
        
    return {
        "request": request, 
        "title": title, 
        "current_user": current_user,
        "active_section": active_section, 
        "BASE_URL": BASE_URL.rstrip('/')
    }

# --- Publicly Accessible UI Routes (as defined in base.html for "EVERYONE") ---

@router.get("/", response_class=HTMLResponse, name="ui_landing_redirect")
async def ui_landing_redirect(request: Request):
    """Redirects /ui/ to the verify agents public page."""
    return RedirectResponse(url=request.app.url_path_for("verify_agents_public"), status_code=303)

@router.get("/verify", response_class=HTMLResponse, name="verify_agents_public")
async def verify_agents_public(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Combined public dashboard and verify agents page."""
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    
    try:
        jwks_data = get_jwks()
        jwks_url_path = "/.well-known/jwks.json"
        try: 
            jwks_url_path = request.app.url_path_for('get_jwks_endpoint')
        except Exception as e: 
            logger.warning(f"Failed to generate JWKS URL for verify page: {e}")
            
        context.update({
            "jwks_url": jwks_url_path,
            "jwks_content_str": json.dumps(jwks_data, indent=2) if jwks_data else "JWKS Not Available",
            "issuer_id": CORE_AIF_SERVICE_ISSUER_ID,
        })
        
        return templates.TemplateResponse("verify_agents_public.html", context)
    except Exception as e:
        logger.error(f"Error rendering verify agents public page: {e}", exc_info=True)
        error_context = get_base_template_context(request, "Error", current_user)
        error_context["error_message"] = f"Could not load verify agents page: {e}"
        return templates.TemplateResponse("error_page.html", error_context, status_code=500)

@router.get("/start-here", response_class=HTMLResponse, name="start_here_page")
async def start_here_page(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Intermediary 'Start Here' page before GitHub login."""
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    return templates.TemplateResponse("start_here.html", context)

@router.get("/revoked-tokens", response_class=HTMLResponse, name="revoked_tokens_check_form")
async def revoked_tokens_check_form(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    jti_to_check: Optional[str] = Query(None, description="The JTI of the token to check for revocation status."),
    status_message: Optional[str] = Query(None),
    message_type: str = Query("info")
):
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    revocation_result_display = None # For displaying results after check
    
    if jti_to_check:
        is_it_revoked = is_jti_revoked(jti_to_check) # Call the function
        if is_it_revoked is None: # DB or other error
            revocation_result_display = f"Error: Could not determine revocation status for JTI: {jti_to_check}."
            if not status_message: status_message = revocation_result_display; message_type = "error"
        else:
            revocation_result_display = f"JTI '{jti_to_check}' is {'REVOKED' if is_it_revoked else 'NOT REVOKED'}."
            if not status_message: status_message = revocation_result_display; message_type = "success" if not is_it_revoked else "warning"
    
    context.update({
        "jti_to_check": jti_to_check, # For repopulating form if needed
        "revocation_result_display": revocation_result_display, # To show the outcome
        "status_message": status_message, # General messages (e.g., from POST redirect)
        "status_message_type": message_type
    })
    return templates.TemplateResponse("revoked_tokens.html", context) # Renders the check form and results

@router.post("/revoked-tokens", name="handle_revoked_tokens_check_form_post")
async def handle_revoked_tokens_check_form_post(request: Request, jti: str = Form(..., min_length=1)):
    # This POST will redirect to the GET route with the JTI to display results
    redirect_url = request.url_for("revoked_tokens_check_form").include_query_params(jti_to_check=jti)
    return RedirectResponse(url=str(redirect_url), status_code=303)

@router.get("/documentation", response_class=HTMLResponse, name="documentation_page")
async def documentation_page(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    context = get_base_template_context(request, "Documentation", current_user)
    return templates.TemplateResponse("documentation.html", context)

# --- READ Section Routes (Always Accessible) ---

@router.get("/api-reference", response_class=HTMLResponse, name="api_reference_page")
async def api_reference_page(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Render the API Reference documentation."""
    context = get_base_template_context(request, "API Reference", current_user)
    
    # Render markdown content
    content = render_markdown_file("api-reference.md")
    if not content:
        content = "<p>API Reference documentation is being prepared. Please check back soon.</p>"
    
    context["content"] = content
    return templates.TemplateResponse("documentation/api_reference.html", context)

@router.get("/whitepaper", response_class=HTMLResponse, name="whitepaper_page")
async def whitepaper_page(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Render the White Paper documentation."""
    context = get_base_template_context(request, "White Paper", current_user)
    
    content = render_markdown_file("whitepaper.md")
    if not content:
        content = "<p>White Paper is being prepared. Please check back soon.</p>"
    
    context["content"] = content
    return templates.TemplateResponse("documentation/whitepaper.html", context)

@router.get("/sdk/agent-builder", response_class=HTMLResponse, name="sdk_agent_builder_page")
async def sdk_agent_builder_page(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Render the Agent Builder SDK documentation."""
    context = get_base_template_context(request, "SDK: Agent Builder", current_user)
    
    content = render_markdown_file("sdk-agent-builder.md")
    if not content:
        content = """
        <p>Agent Builder SDK documentation is being prepared.</p>
        <p>For now, you can:</p>
        <ul>
            <li>Use the web interface to issue and revoke tokens</li>
            <li>Use the <a href="/ui/api-reference">API Reference</a> for direct API integration</li>
            <li>Check back soon for the Python SDK</li>
        </ul>
        """
    
    context["content"] = content
    return templates.TemplateResponse("documentation/sdk_agent_builder.html", context)

@router.get("/sdk/service-providers", response_class=HTMLResponse, name="sdk_service_provider_page")
async def sdk_service_provider_page(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Render the Service Provider SDK documentation."""
    context = get_base_template_context(request, "SDK: Service Providers", current_user)
    
    content = render_markdown_file("sdk-service-providers.md")
    if not content:
        content = """
        <p>Service Provider SDK documentation is being prepared.</p>
        <p>For now, you can:</p>
        <ul>
            <li>Check the <a href="https://github.com/IAM-Heimdall/heimdall-sp-validator-sdk-python" target="_blank">Python Validator SDK</a></li>
            <li>Use the <a href="/.well-known/jwks.json">JWKS endpoint</a> to get public keys</li>
            <li>Reference the <a href="/ui/api-reference">API Reference</a> for validation patterns</li>
        </ul>
        """
    
    context["content"] = content
    return templates.TemplateResponse("documentation/sdk_service_providers.html", context)

# --- Authenticated User Routes ---

@router.get("/dashboard", response_class=HTMLResponse, name="ui_dashboard_dispatch")
async def ui_dashboard_dispatch(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    
    if not current_user:
        # For non-authenticated users, redirect to the combined verify agents / public dashboard
        return RedirectResponse(url=request.app.url_path_for("verify_agents_public"), status_code=303)

    user_role = getattr(current_user, 'role', "agent_builder")
    if user_role == "agent_builder":
        ab_profile_dict = get_agent_builder_by_user_id(str(current_user.id))
        if not ab_profile_dict:
            logger.error(f"AB profile dict not found for user ID: {current_user.id}")
            raise HTTPException(status_code=404, detail="Agent Builder profile missing.")
        
        # Get API token info
        api_token = getattr(current_user, 'api_token', None)
        
        issued_tokens_list = get_user_issued_tokens(user_id=str(current_user.id), limit=10)
        days_until_expiry = None
        
        # Check token expiry
        api_token_expiry_dt = getattr(current_user, 'api_token_expires_at', None)
        if api_token_expiry_dt:
            if api_token_expiry_dt.tzinfo is None:
                api_token_expiry_dt_aware = api_token_expiry_dt.replace(tzinfo=timezone.utc)
            else:
                api_token_expiry_dt_aware = api_token_expiry_dt

            now_utc = datetime.now(timezone.utc)
            delta = api_token_expiry_dt_aware - now_utc
            days_until_expiry = delta.days
        
        context.update({
            "api_token": api_token,
            "days_until_expiry": days_until_expiry,
            "issued_tokens": issued_tokens_list,
            "organization_name": getattr(current_user, 'organization_name', None) or getattr(current_user, 'name', 'User')
        })
        
        return templates.TemplateResponse("agent_creator_dashboard.html", context)
    else: 
        context["message"] = "Welcome. Your role-specific dashboard is under construction."
        return templates.TemplateResponse("agent_creator_dashboard.html", context)

@router.post("/generate-token")
async def generate_token_api(request: Request, user: User = Depends(require_agent_builder)):
    """API endpoint to generate a new API token."""
    try:
        user_id = str(user.id)
        updated_user = regenerate_api_token(user_id)
        
        if not updated_user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Failed to regenerate API token"}
            )
        
        return JSONResponse(
            content={
                "success": True,
                "api_token": updated_user["api_token"],
                "expires_at": updated_user["api_token_expires_at"].isoformat() if updated_user.get("api_token_expires_at") else None
            }
        )
    except Exception as e:
        logger.error(f"Error generating token via API: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/profile", response_class=HTMLResponse, name="profile_page")
async def profile_page(request: Request, current_user: User = Depends(require_authenticated_user)):
    """User profile page."""
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    
    # Get user attributes with safe fallbacks
    api_token = getattr(current_user, 'api_token', None)
    api_token_expires_at = getattr(current_user, 'api_token_expires_at', None)
    created_at = getattr(current_user, 'created_at', None)
    
    context.update({
        "organization_name": getattr(current_user, 'organization_name', 'N/A'),
        "email": getattr(current_user, 'email', 'N/A'),
        "website": getattr(current_user, 'website', "Not set") or "Not set",
        "created_at": created_at,
        "created_at_str": created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if created_at else "N/A",
        "api_token_masked": f"{api_token[:10]}...{api_token[-5:]}" if api_token else "Not Generated",
        "api_token_expires_at": api_token_expires_at,
        "api_token_expires_at_str": api_token_expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if api_token_expires_at else "N/A"
    })
    
    return templates.TemplateResponse("profile.html", context)

# --- Agent Builder Specific UI Routes ---

@router.get("/issue-token", response_class=HTMLResponse, name="issue_token_form_get")
async def issue_token_form_get(request: Request, current_user: User = Depends(require_agent_builder)):
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    issued_tokens_list = get_user_issued_tokens(user_id=str(current_user.id), status="active", limit=10)
    context.update({
        "supported_models": SUPPORTED_AI_MODELS,
        "standard_permissions": STANDARD_PERMISSIONS_LIST,
        "default_trust_tags_info": DEFAULT_AIF_TRUST_TAGS if DEFAULT_AIF_TRUST_TAGS is not None else {},
        "form_data": {},
        "issued_tokens": issued_tokens_list
    })
    return templates.TemplateResponse("issue_token_ui.html", context)

@router.post("/issue-token", response_class=HTMLResponse, name="issue_token_form_post")
async def issue_token_form_post(
    request: Request, current_user: User = Depends(require_agent_builder),
    user_id: str = Form(..., min_length=1), audience_sp_id: str = Form(..., min_length=1),
    input_permissions_str: str = Form(..., alias="permissions", min_length=1),
    purpose: str = Form(..., min_length=1), model_id: str = Form(...)
):
    context = get_base_template_context(request, "Issue New ATK", current_user)
    form_data_repopulate = {
        "user_id": user_id, "audience_sp_id": audience_sp_id,
        "permissions_str": input_permissions_str, "purpose": purpose, "model_id": model_id
    }
    message, message_type, issued_atk_val = "", "error", None
    try:
        if not all([user_id, audience_sp_id, input_permissions_str, purpose, model_id]):
            raise ValueError("All fields required.")
        actual_permissions = [p.strip() for p in input_permissions_str.split(',') if p.strip()]
        if not actual_permissions: raise ValueError("At least one permission required.")

        signed_atk = create_atk(
            user_id=user_id.strip(), audience_sp_id=audience_sp_id.strip(),
            permissions=actual_permissions, purpose=purpose.strip(),
            model_id=model_id.strip(), override_trust_tags=None # Simplified for PoC UI
        )
        if signed_atk:
            issued_atk_val = signed_atk
            message = "✅ ATK issued successfully!"
            if DEFAULT_AIF_TRUST_TAGS: message += f" (Defaults: {json.dumps(DEFAULT_AIF_TRUST_TAGS)})"
            else: message += " (No default trust tags.)"
            message_type = "success"
            try:
                # Ensure PyJWT is used for decoding if that's what you settled on
                decoded_token = jwt.decode(signed_atk, options={"verify_signature": False, "verify_exp": False, "verify_aud": False})
                token_record = {
                    "aid": decoded_token.get("sub"), "jti": decoded_token.get("jti"),
                    "issued_at": datetime.fromtimestamp(decoded_token.get("iat"), tz=timezone.utc),
                    "expires_at": datetime.fromtimestamp(decoded_token.get("exp"), tz=timezone.utc),
                    "audience": audience_sp_id.strip(), "permissions": actual_permissions,
                    "purpose": purpose.strip(), "model_id": model_id.strip(), "status": "active"
                }
                add_issued_token_record(str(current_user.id), token_record)
            except Exception as e: logging.warning(f"Could not record issued token: {e}", exc_info=True)
            form_data_repopulate = {"model_id": model_id} # Clear form
        else: message = "❌ Failed to issue ATK. Logs may have details."
    except ValueError as e: message = f"❌ Validation error: {str(e)}"
    except Exception as e:
        logging.error(f"Error issuing token UI: {e}", exc_info=True)
        message = "❌ Unexpected error issuing token."

    issued_tokens_list = get_user_issued_tokens(user_id=str(current_user.id), status="active", limit=10)
    context.update({
        "message": message, "message_type": message_type, "issued_atk": issued_atk_val,
        "supported_models": SUPPORTED_AI_MODELS, "standard_permissions": STANDARD_PERMISSIONS_LIST,
        "default_trust_tags_info": DEFAULT_AIF_TRUST_TAGS or {}, "form_data": form_data_repopulate,
        "issued_tokens": issued_tokens_list
    })
    return templates.TemplateResponse("issue_token_ui.html", context)

@router.get("/revoke-token", response_class=HTMLResponse, name="revoke_token_form_get")
async def revoke_token_form_get(
    request: Request, current_user: User = Depends(require_agent_builder),
    message: Optional[str] = None, msg_type: Optional[str] = "info"
):
    context = get_base_template_context(request, "IAM Heimdall", current_user)
    revoked_tokens_list_display = []
    try:
        revoked_tokens_list_raw = get_revoked_tokens(agent_builder_id=str(current_user.id), limit=20)
        for item_raw in revoked_tokens_list_raw:
            item = dict(item_raw)
            # Ensure correct datetime conversion for template
            if item.get("original_exp_ts") and not isinstance(item["original_exp_ts"], datetime):
                try: item["original_exp_ts_dt"] = datetime.fromtimestamp(item["original_exp_ts"], tz=timezone.utc)
                except: item["original_exp_ts_dt"] = "Invalid Ts"
            elif isinstance(item.get("original_exp_ts"), datetime): item["original_exp_ts_dt"] = item["original_exp_ts"]
            else: item["original_exp_ts_dt"] = None
            revoked_tokens_list_display.append(item)
    except Exception as e:
        logging.error(f"Error fetching AB's revoked tokens: {e}", exc_info=True)
        if not message: message = "Error fetching your revocation list."; msg_type = "error"
    context.update({"revoked_tokens": revoked_tokens_list_display, "message": message, "message_type": msg_type})
    return templates.TemplateResponse("revoke_token_ui.html", context)

@router.post("/revoke-token", name="revoke_token_form_post")
async def revoke_token_form_post(
    request: Request, current_user: User = Depends(require_agent_builder),
    jti: str = Form(..., min_length=1)
):
    message, msg_type = "", "error"
    try:
        if not jti.strip(): raise ValueError("JTI cannot be empty.")
        success = add_jti_to_revocation_list(jti=jti.strip(), agent_builder_id=str(current_user.id))
        if success: message, msg_type = f"✅ JTI '{jti}' processed for revocation.", "success"
        else: message = f"❌ Failed to add JTI '{jti}' to revocation list."
    except ValueError as e: message = f"❌ Validation Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error revoking token via UI: {e}", exc_info=True)
        message = f"❌ Unexpected error revoking JTI '{jti}'."
    redirect_url = request.url_for("revoke_token_form_get").include_query_params(message=message, msg_type=msg_type)
    return RedirectResponse(url=str(redirect_url), status_code=303)

# --- Registration Routes ---
@router.get("/register/agent-builder", response_class=HTMLResponse, name="register_agent_builder_form_get")
async def register_agent_builder_form_get(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    context = get_base_template_context(request, "Register as Agent Builder", current_user)
    return templates.TemplateResponse("registration_ab.html", context)

@router.post("/register/agent-builder", response_class=HTMLResponse, name="register_agent_builder_form_post")
async def register_agent_builder_form_post(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    context = get_base_template_context(request, "Agent Builder Registration", current_user)
    context["message"], context["message_type"] = "Agent Builder registration (Placeholder).", "info"
    return templates.TemplateResponse("registration_ab.html", context)

@router.get("/register/service-provider", response_class=HTMLResponse, name="register_service_provider_form_get")
async def register_service_provider_form_get(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    context = get_base_template_context(request, "Register as Service Provider", current_user)
    return templates.TemplateResponse("registration_sp.html", context)

@router.post("/register/service-provider", response_class=HTMLResponse, name="register_service_provider_form_post")
async def register_service_provider_form_post(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    context = get_base_template_context(request, "Service Provider Registration", current_user)
    context["message"], context["message_type"] = "Service Provider registration (Placeholder).", "info"
    return templates.TemplateResponse("registration_sp.html", context)