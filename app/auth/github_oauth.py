# app/auth/github_oauth.py
import os
import secrets
from urllib.parse import urlencode
import httpx
from fastapi import Request, HTTPException
import logging
import jwt
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from typing import Optional

from app.db.user_store import get_user_by_github_id, get_user_by_id
from app.auth.token_utils import generate_api_token
from config.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, JWT_SECRET_KEY, BASE_URL

# GitHub OAuth Configuration
GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"
GITHUB_USER_EMAILS_API = "https://api.github.com/user/emails"

logger = logging.getLogger(__name__)

def get_github_auth_url(request: Request) -> str:
    """Generate GitHub OAuth URL with state parameter for CSRF protection."""
    state = secrets.token_urlsafe(32)
    
    # Store state in session
    request.session["oauth_state"] = state
    
    # Build GitHub OAuth URL
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/auth/github/callback",
        "scope": "user:email",
        "state": state
    }
    
    return f"{GITHUB_OAUTH_URL}?{urlencode(params)}"

async def github_callback_handler(code: str, state: str, request: Request):
    """
    Handle GitHub OAuth callback.
    
    Args:
        code: Authorization code from GitHub
        state: State parameter for CSRF validation
        request: FastAPI request object
    
    Returns:
        User object if successful
        None if user needs to complete registration
    
    Raises:
        HTTPException: If OAuth process fails
    """
    # Verify state parameter
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        logger.warning("GitHub OAuth: Invalid state parameter")
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": f"{BASE_URL}/auth/github/callback"
                },
                headers={"Accept": "application/json"},
                timeout=10.0  # Add timeout
            )
            
            token_response.raise_for_status()  # Raise for HTTP errors
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("GitHub OAuth: No access token received")
                raise HTTPException(status_code=400, detail="No access token received")
            
            # Fetch user information
            user_response = await client.get(
                GITHUB_USER_API,
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json"
                },
                timeout=10.0
            )
            
            user_response.raise_for_status()
            github_user = user_response.json()
            
            # Fetch user emails if email is not public
            user_email = github_user.get("email")
            if not user_email:
                email_response = await client.get(
                    GITHUB_USER_EMAILS_API,
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json"
                    },
                    timeout=10.0
                )
                
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_emails = [e for e in emails if e.get("primary")]
                    if primary_emails:
                        user_email = primary_emails[0].get("email")
                    elif emails:
                        user_email = emails[0].get("email")
        
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=400, detail=f"GitHub API error: {e.response.reason_phrase}")
        
        except httpx.RequestError as e:
            logger.error(f"GitHub API request error: {str(e)}")
            raise HTTPException(status_code=500, detail="Error connecting to GitHub API")
        
        # Clean up session
        request.session.pop("oauth_state", None)
        
        # Check if user exists
        github_id = str(github_user["id"])
        existing_user = get_user_by_github_id(github_id)
        
        if existing_user:
            # User exists - check if registration is complete
            if existing_user.get("registration_complete", False):
                # Registration is complete, create session
                create_session(request, existing_user)
                return existing_user
            else:
                # Registration is incomplete, store GitHub data and redirect
                request.session["github_user"] = {
                    "github_id": github_id,
                    "github_username": github_user.get("login"),
                    "name": github_user.get("name") or github_user.get("login"),
                    "email": user_email,
                    "avatar_url": github_user.get("avatar_url")
                }
                
                # Store user ID in session
                request.session["user_id"] = str(existing_user["_id"])
                return None
        else:
            # New user - store GitHub info and continue to registration
            new_user = create_github_user({
                "github_id": github_id,
                "github_username": github_user.get("login"),
                "name": github_user.get("name") or github_user.get("login"),
                "email": user_email,
                "avatar_url": github_user.get("avatar_url"),
                "created_at": datetime.now(timezone.utc),
                "registration_complete": False
            })
            
            if not new_user:
                logger.error(f"Failed to create user for GitHub ID: {github_id}")
                raise HTTPException(status_code=500, detail="User creation failed")
            
            # Store user in session for registration completion
            request.session["github_user"] = {
                "github_id": github_id,
                "github_username": github_user.get("login"),
                "name": github_user.get("name") or github_user.get("login"),
                "email": user_email,
                "avatar_url": github_user.get("avatar_url")
            }
            
            # Store user ID in session
            request.session["user_id"] = str(new_user["_id"])
            return None

def create_github_user(user_data: dict) -> Optional[dict]:
    """
    Create a new user from GitHub authentication.
    This replaces the missing function from user_store.py
    """
    try:
        from app.db.mongo_client import get_db
        
        collection = get_db()["users"]
        
        # Check if user already exists
        existing = collection.find_one({"github_id": user_data["github_id"]})
        if existing:
            return existing
        
        # Set default values if not provided
        if "created_at" not in user_data:
            user_data["created_at"] = datetime.now(timezone.utc)
            
        if "registration_complete" not in user_data:
            user_data["registration_complete"] = False
        
        # Insert user
        result = collection.insert_one(user_data)
        
        if result.inserted_id:
            created_user = collection.find_one({"_id": result.inserted_id})
            return created_user
        return None
    except Exception as e:
        logger.error(f"Error creating GitHub user: {e}")
        return None

def create_session(request: Request, user: dict):
    """Create a session for authenticated user."""
    session_token = create_session_token(user)
    request.session["user_id"] = str(user["_id"])
    request.session["authenticated"] = True
    return session_token

def create_session_token(user: dict) -> str:
    """Create a JWT session token for the user."""
    payload = {
        "user_id": str(user["_id"]),
        "github_id": user["github_id"],
        "type": "session_token",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7)  # 7 day session
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def verify_session_token(token: str) -> Optional[dict]:
    """Verify and decode a session token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Session token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid session token: {e}")
        return None

def generate_api_token(user_id: str) -> tuple[str, datetime]:
    """Generate a new API token for Agent Builder."""
    expiry = datetime.now(timezone.utc) + timedelta(days=90)  # 90 day token
    payload = {
        "user_id": user_id,
        "type": "api_token",
        "iat": datetime.now(timezone.utc),
        "exp": expiry
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token, expiry