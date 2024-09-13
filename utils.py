import hashlib
import hmac
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")

def hash_id(user_id):
    """Generate a HMAC hash of the user ID using a secret key."""
    return hmac.new(SECRET_KEY.encode(), user_id.encode(), hashlib.sha256).hexdigest()

def check_hashed_id(hashed_id, user_id):
    """Validate that a given hashed ID matches the user ID."""
    return hmac.compare_digest(hashed_id, hash_id(user_id))

