from flask import Blueprint, request, session
from app.models.user import create_user, get_user_by_username, verify_password

bp = Blueprint("auth", __name__)

@bp.post("/register")
def register():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return {"error": "username and password required"}, 400

    if get_user_by_username(username):
        return {"error": "username already exists"}, 409

    create_user(username, password, role="USER")
    return {"status": "registered"}, 201


@bp.post("/login")
def login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = get_user_by_username(username)
    if not user or not verify_password(user, password):
        return {"error": "invalid credentials"}, 401

    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["username"] = user["username"]
    return {"status": "logged_in", "role": user["role"]}


@bp.post("/logout")
def logout():
    session.clear()
    return {"status": "logged_out"}