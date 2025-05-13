# app/db/__init__.py
from .mongo_client import get_db, close_db_connection, ensure_db_indexes
from .revocation_store import add_jti_to_revocation_list, is_jti_revoked

# Expose functions for easy import from 'app.db'
__all__ = [
    "get_db",
    "close_db_connection",
    "ensure_db_indexes",
    "add_jti_to_revocation_list",
    "is_jti_revoked"
]