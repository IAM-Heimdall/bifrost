# app/auth/middleware.py
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt # Using PyJWT for API token validation
import logging

from app.db.user_store import get_user_by_id # This returns a dict or None
from app.models.user_models import User    # Import your Pydantic User model
from config.settings import JWT_SECRET_KEY, BASE_URL # BASE_URL for redirect construction

logger = logging.getLogger(__name__)

# auto_error=False allows the route to handle the case where the header is missing,
# otherwise FastAPI would immediately return a 403 if the header is absent.
security = HTTPBearer(auto_error=False)

async def get_current_user(request: Request) -> Optional[User]:
    """
    Extracts current user_id from session, fetches user data from DB,
    and returns a User Pydantic model instance.
    Returns None if not authenticated or user not found.
    """
    if request.session.get("authenticated") is not True:
        return None
    
    user_id_str = request.session.get("user_id")
    if not user_id_str:
        logger.debug("No user_id found in session for get_current_user.")
        return None
    
    try:
        user_data_from_db = get_user_by_id(user_id_str) # Fetches dict from MongoDB
        if user_data_from_db:
            # Convert MongoDB dict (with _id) to Pydantic User model instance
            return User(**user_data_from_db)
        else:
            logger.warning(f"User ID '{user_id_str}' in session but not found in DB. Clearing session.")
            request.session.clear() # Good practice to clear inconsistent session
            return None
    except Exception as e:
        logger.error(f"Error retrieving user (ID: {user_id_str}) from session or converting to model: {e}", exc_info=True)
        return None

async def get_optional_current_user(request: Request) -> Optional[User]:
    """Dependency to get current user if authenticated, otherwise None. Does not raise HTTPExceptions."""
    return await get_current_user(request)

async def require_authenticated_user(request: Request) -> User:
    """
    Dependency that requires a user to be authenticated.
    If not, redirects to login. If authenticated but registration incomplete, redirects to complete registration.
    Returns the User Pydantic model instance.
    """
    user = await get_current_user(request)
    if not user:
        request.session["next_url"] = str(request.url)
        login_url = request.app.url_path_for("github_login") # Assumes this route name
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": str(login_url)})
    
    if not user.registration_complete:
        complete_reg_url = request.app.url_path_for("register_complete_form") # Assumes this route name
        if str(request.url.path) != str(complete_reg_url): # Check full path
            request.session["next_url"] = str(request.url)
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": str(complete_reg_url)})
    return user

# Alias for convenience or backward compatibility
require_auth = require_authenticated_user

async def require_agent_builder(user: User = Depends(require_authenticated_user)) -> User:
    """
    Dependency that requires the authenticated user to have the 'agent_builder' role.
    Relies on require_authenticated_user to handle initial auth and registration completion.
    """
    if user.role != "agent_builder": # Direct attribute access is safe due to Pydantic model
        logger.warning(f"User '{user.id}' (Role: '{user.role}') attempted Agent Builder action. Access denied.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent Builder role required for this action.")
    return user

async def require_service_provider(user: User = Depends(require_authenticated_user)) -> User:
    """
    Dependency that requires the authenticated user to have the 'service_provider' role.
    """
    if user.role != "service_provider": # Direct attribute access
        logger.warning(f"User '{user.id}' (Role: '{user.role}') attempted Service Provider action. Access denied.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service Provider role required.")
    return user

async def validate_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Validates an API token from the Authorization header.
    Returns a User Pydantic model instance if valid, otherwise None.
    """
    if not credentials:
        return None # No token provided
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        
        if payload.get("type") != "api_token":
            logger.warning("Invalid token type in API request (not 'api_token').")
            return None
        
        user_id_from_token = payload.get("user_id")
        if not user_id_from_token:
            logger.warning("API token payload missing 'user_id'.")
            return None
        
        user_data_from_db = get_user_by_id(user_id_from_token) # Returns dict
        if not user_data_from_db:
            logger.warning(f"User {user_id_from_token} from API token not found in DB.")
            return None
        
        # Critical: Verify the presented token matches the one currently stored for the user
        if user_data_from_db.get("api_token") != token:
            logger.warning(f"Presented API token does not match stored API token for user {user_id_from_token}.")
            return None # This invalidates old tokens if a new one was generated
        
        return User(**user_data_from_db) # Convert dict to User Pydantic model
        
    except jwt.ExpiredSignatureError:
        logger.info(f"Attempt to use an expired API token (user_id from potential payload: {payload.get('user_id', 'N/A') if 'payload' in locals() else 'N/A'}).")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid API token presented: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating API token: {e}", exc_info=True)
        return None

async def require_api_auth(user: Optional[User] = Depends(validate_api_token)) -> User:
    """
    Dependency that requires valid API token authentication.
    Relies on validate_api_token to provide the User model instance or None.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""}, # Standard for Bearer tokens
        )
    
    if not user.registration_complete: # Direct attribute access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account registration is incomplete. API access denied."
        )
    return user