from functools import wraps
from flask import session

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return {"error": "authentication required"}, 401
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return {"error": "authentication required"}, 401
        if session.get("role") != "ADMIN":
            return {"error": "admin only"}, 403
        return fn(*args, **kwargs)
    return wrapper
