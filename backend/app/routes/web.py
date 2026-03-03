from flask import Blueprint, render_template, request, redirect, url_for, session

from app.models.user import create_user, get_user_by_username, verify_password
from app.models.submission import (
    create_submission,
    get_submission,
    list_all_submissions,
    list_user_submissions,
    update_status,
)
from app.utils.authz import login_required, admin_required

import os
from datetime import datetime

bp = Blueprint("web", __name__)

@bp.get("/")
def home():
    # Redirection intelligente
    if session.get("role") == "ADMIN":
        return redirect(url_for("web.admin_submissions"))
    if session.get("user_id"):
        return redirect(url_for("web.submit_page"))
    return redirect(url_for("web.login_page"))


@bp.get("/web/login")
def login_page():
    return render_template("login.html", error=None)

@bp.post("/web/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = get_user_by_username(username)
    if not user or not verify_password(user, password):
        return render_template("login.html", error="Identifiants invalides.")

    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["username"] = user["username"]

    return redirect(url_for("web.home"))


@bp.post("/web/logout")
def logout():
    session.clear()
    return redirect(url_for("web.login_page"))


@bp.get("/web/register")
def register_page():
    return render_template("register.html", error=None)

@bp.post("/web/register")
def register_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template("register.html", error="Username et mot de passe requis.")

    if get_user_by_username(username):
        return render_template("register.html", error="Ce username existe déjà.")

    create_user(username, password, role="USER")
    return redirect(url_for("web.login_page"))


@bp.get("/web/submit")
@login_required
def submit_page():
    user_id = session["user_id"]
    sid = request.args.get("sid", type=int)
    result = get_submission(sid) if sid else None
    submissions = list_user_submissions(user_id)
    return render_template(
        "submit.html",
        username=session.get("username"),
        result=result,
        submissions=submissions,
        error=None,
    )

@bp.post("/web/submit")
@login_required
def submit_post():
    code = request.form.get("code", "")
    if not code.strip():
        user_id = session["user_id"]
        submissions = list_user_submissions(user_id)
        return render_template(
            "submit.html",
            username=session.get("username"),
            result=None,
            submissions=submissions,
            error="Code requis.",
        )

    user_id = session["user_id"]

    base_dir = "/app/storage/submissions"
    os.makedirs(base_dir, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"user{user_id}_{ts}.py"
    file_path = os.path.join(base_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    created = create_submission(user_id, file_path)
    return redirect(url_for("web.submit_page", sid=created["id"]))


@bp.get("/web/my-submissions")
@login_required
def my_submissions():
    user_id = session["user_id"]
    subs = list_user_submissions(user_id)
    return render_template(
        "my_submissions.html",
        username=session.get("username"),
        submissions=subs,
    )


@bp.get("/web/admin/submissions")
@admin_required
def admin_submissions():
    subs = list_all_submissions()
    return render_template("admin_submissions.html", username=session.get("username"), submissions=subs)

@bp.post("/web/admin/submissions/<int:sid>/approve")
@admin_required
def admin_approve(sid: int):
    update_status(sid, "APPROVED")
    return redirect(url_for("web.admin_submissions"))

@bp.post("/web/admin/submissions/<int:sid>/reject")
@admin_required
def admin_reject(sid: int):
    update_status(sid, "REJECTED")
    return redirect(url_for("web.admin_submissions"))