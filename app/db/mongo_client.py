# app/db/mongo_client.py
import os
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from typing import Optional

# Import configurations from settings.py
from config.settings import MONGO_DATABASE_URL, MONGO_DATABASE_NAME

_db_client: Optional[MongoClient] = None
_db: Optional[Database] = None

def get_db() -> Database:
    """
    Provides a MongoDB database instance.
    Initializes the client connection if it doesn't exist.
    """
    global _db_client, _db
    if _db is None:
        print(f"🔄 Initializing MongoDB connection to {MONGO_DATABASE_URL} / DB: {MONGO_DATABASE_NAME}...")
        try:
            _db_client = MongoClient(MONGO_DATABASE_URL, serverSelectionTimeoutMS=5000) # Added timeout
            # The ismaster command is cheap and does not require auth.
            _db_client.admin.command('ismaster') # Verifies connection
            _db = _db_client[MONGO_DATABASE_NAME]
            print(f"✅ Successfully connected to MongoDB: {MONGO_DATABASE_NAME}")
        except ConnectionFailure as e:
            print(f"❌ CRITICAL ERROR: Could not connect to MongoDB at {MONGO_DATABASE_URL}.")
            print(f"   Error details: {e}")
            raise
        except Exception as e:
            print(f"❌ CRITICAL ERROR: An unexpected error occurred during MongoDB connection: {e}")
            raise
    return _db

def close_db_connection():
    """Closes the MongoDB connection if it's open."""
    global _db_client, _db
    if _db_client:
        print("🚪 Closing MongoDB connection...")
        _db_client.close()
        _db_client = None
        _db = None
        print("✅ MongoDB connection closed.")

# Ensure collections and indexes are created on startup if they don't exist
def ensure_db_indexes(db_instance: Database):
    """
    Ensures necessary indexes are created in MongoDB collections.
    Call this once at application startup after getting the DB instance.
    """
    print("🔧 Ensuring database indexes...")
    try:
        # For revoked_atks collection
        revoked_tokens_collection_name = os.getenv("REVOKED_TOKENS_COLLECTION_NAME", "revoked_atks") # Get from settings if used elsewhere
        revoked_collection = db_instance[revoked_tokens_collection_name]
        
        # Index on 'jti' for fast lookups, ensure uniqueness
        if "jti_1" not in revoked_collection.index_information():
            revoked_collection.create_index("jti", unique=True, name="jti_1")
            print(f"   ✅ Index 'jti_1' created for collection '{revoked_tokens_collection_name}'.")
        else:
            print(f"   👍 Index 'jti_1' already exists for collection '{revoked_tokens_collection_name}'.")

        # Optional: TTL index on 'revoked_at' or 'original_exp' for automatic cleanup of old revoked tokens
        # This is more advanced and depends on your cleanup strategy. Example:
        # if "revoked_at_ttl_1" not in revoked_collection.index_information():
        #     # Expire documents 30 days after they were revoked (adjust as needed)
        #     revoked_collection.create_index("revoked_at", expireAfterSeconds=30*24*60*60, name="revoked_at_ttl_1")
        #     print(f"   ✅ TTL Index 'revoked_at_ttl_1' created for collection '{revoked_tokens_collection_name}'.")

        # Add index creation for other collections as they are introduced in Phase 2
        print("✅ Database index check complete.")

    except PyMongoError as e:
        print(f"❌ MongoDB Error during index creation: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during index creation: {e}")

# Example of how to call ensure_db_indexes in app startup (e.g., in app/__init__.py or run.py)
# db = get_db()
# ensure_db_indexes(db)