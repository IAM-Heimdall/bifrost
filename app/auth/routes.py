from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging
from pathlib import Path

from app.auth.github_oauth import get_github_auth_url, github_callback_handler
from app.auth.middleware import get_current_user, require_auth
from app.db.user_store import complete_user_registration, regenerate_api_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Templates directory
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

logger = logging.getLogger(__name__)

@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth login."""
    # Check if there's a next URL to redirect to after login
    if "next" in request.query_params:
        request.session["next_url"] = request.query_params["next"]
    
    # Get GitHub auth URL
    auth_url = get_github_auth_url(request)
    return RedirectResponse(url=auth_url)

@router.get("/github/callback")
async def github_callback(request: Request, code: str, state: str):
    """Handle GitHub OAuth callback."""
    try:
        # Process GitHub callback
        user = await github_callback_handler(code, state, request)
        
        if user is None:
            # Redirect to registration completion
            return RedirectResponse(url="/auth/register/complete", status_code=303)
        
        # Get next URL from session or default to dashboard
        next_url = request.session.pop("next_url", "/ui/dashboard")
        
        return RedirectResponse(url=next_url, status_code=303)
    
    except HTTPException as e:
        logger.error(f"GitHub callback error: {e.detail}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Authentication Error",
                "error_message": e.detail
            },
            status_code=e.status_code
        )

@router.get("/register/complete", response_class=HTMLResponse)
async def register_complete_form(request: Request):
    """Display registration completion form."""
    # Check if there's GitHub user data in session
    github_user = request.session.get("github_user")
    if not github_user:
        return RedirectResponse(url="/auth/github/login", status_code=303)
    
    return templates.TemplateResponse(
        "register_complete.html",
        {
            "request": request,
            "title": "Complete Registration",
            "github_user": github_user
        }
    )

@router.post("/register/complete")
async def register_complete_submit(
    request: Request,
    organization_name: str = Form(...),
    website: Optional[str] = Form(None)
):
    """Handle registration completion submission."""
    # Check if there's GitHub user data in session
    github_user = request.session.get("github_user")
    if not github_user:
        return RedirectResponse(url="/auth/github/login", status_code=303)
    
    # Get user from database
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/github/login", status_code=303)
    
    # Complete registration
    registration_data = {
        "organization_name": organization_name,
        "website": website
    }
    
    updated_user = complete_user_registration(user_id, registration_data)
    if not updated_user:
        return templates.TemplateResponse(
            "register_complete.html",
            {
                "request": request,
                "title": "Complete Registration",
                "github_user": github_user,
                "error": "Failed to complete registration. Please try again."
            }
        )
    
    # Clear GitHub user data from session
    request.session.pop("github_user", None)
    
    # Set authenticated in session
    request.session["authenticated"] = True
    
    # Redirect to dashboard
    return RedirectResponse(url="/ui/dashboard", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    """Log out the current user."""
    # Clear session
    request.session.clear()
    
    return RedirectResponse(url="/", status_code=303)

@router.post("/regenerate-token")
async def regenerate_token(request: Request, user: dict = Depends(require_auth)):
    """Regenerate API token for the current user."""
    user_id = str(user["_id"])
    
    # Regenerate token
    updated_user = regenerate_api_token(user_id)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to regenerate API token")
    
    # Return the new token
    return {
        "api_token": updated_user["api_token"],
        "expires_at": updated_user["api_token_expires_at"]
    }