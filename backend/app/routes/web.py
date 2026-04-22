from flask import Blueprint, render_template, request, redirect, url_for, session

from app.models.user import create_user, get_user_by_username, verify_password
from app.models.submission import (
    create_submission,
    get_submission,
    get_submission_by_id,
    get_user_submission,
    list_all_submissions,
    list_user_submissions,
    update_status,
)
from app.models.microdata import list_microdata_files
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
    search = request.args.get("q", "").strip() or None
    result = get_submission(sid) if sid else None
    submissions = list_user_submissions(user_id, search=search)
    microdata_files = list_microdata_files()
    return render_template(
        "submit.html",
        username=session.get("username"),
        result=result,
        submissions=submissions,
        search=search,
        microdata_files=microdata_files,
        error=None,
    )

@bp.post("/web/submit")
@login_required
def submit_post():
    code = request.form.get("code", "")
    name = request.form.get("name", "").strip() or None
    microdata_guid = request.form.get("microdata_guid", "").strip() or None
    language = request.form.get("language", "python").strip()

    user_id = session["user_id"]

    if not code.strip():
        submissions = list_user_submissions(user_id)
        microdata_files = list_microdata_files()
        return render_template(
            "submit.html",
            username=session.get("username"),
            result=None,
            submissions=submissions,
            microdata_files=microdata_files,
            search=None,
            error="Code requis.",
        )

    base_dir = "/app/storage/submissions"
    os.makedirs(base_dir, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in (name or "script"))
    ext = ".R" if language == "r" else ".py"
    filename = f"user{user_id}_{ts}_{safe_name}{ext}"
    file_path = os.path.join(base_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    created = create_submission(user_id, file_path, name=name, microdata_guid=microdata_guid)
    return redirect(url_for("web.submit_page", sid=created["id"]))


@bp.get("/web/my-submissions")
@login_required
def my_submissions():
    user_id = session["user_id"]
    search = request.args.get("q", "").strip() or None
    subs = list_user_submissions(user_id, search=search)
    return render_template(
        "my_submissions.html",
        username=session.get("username"),
        submissions=subs,
        search=search,
    )


@bp.get("/web/my-submissions/<int:sid>")
@login_required
def user_view_submission(sid: int):
    user_id = session["user_id"]
    sub = get_user_submission(user_id, sid)
    if not sub:
        return redirect(url_for("web.submit_page"))

    code_content = ""
    file_path = sub["file_path"]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()
    except FileNotFoundError:
        code_content = "# Fichier introuvable"

    return render_template(
        "user_view_submission.html",
        username=session.get("username"),
        submission=sub,
        code_content=code_content,
    )


@bp.get("/web/admin/submissions")
@admin_required
def admin_submissions():
    subs = list_all_submissions()
    return render_template("admin_submissions.html", username=session.get("username"), submissions=subs)


@bp.get("/web/admin/submissions/<int:sid>")
@admin_required
def admin_view_submission(sid: int):
    sub = get_submission_by_id(sid)
    if not sub:
        return redirect(url_for("web.admin_submissions"))

    code_content = ""
    file_path = sub["file_path"]
    local_path = file_path.replace("/app/storage", "/app/storage")
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            code_content = f.read()
    except FileNotFoundError:
        code_content = "# Fichier introuvable"

    return render_template(
        "admin_view_submission.html",
        username=session.get("username"),
        submission=sub,
        code_content=code_content,
    )


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