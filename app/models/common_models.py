# app/models/common_models.py
from pydantic import BaseModel
from typing import Optional

class MessageResponse(BaseModel):
    """
    A generic message response model.
    Useful for simple success/error messages from API endpoints.
    """
    message: str
    detail: Optional[str] = None
    status_code: Optional[int] = None # For conveying HTTP status in the body if needed