from flask import Blueprint
from app.utils.authz import admin_required
from app.models.submission import list_all_submissions, update_status

bp = Blueprint("admin", __name__)

@bp.get("/admin/submissions")
@admin_required
def all_submissions():
    return {"submissions": list_all_submissions()}

@bp.post("/admin/submissions/<int:sid>/approve")
@admin_required
def approve(sid: int):
    update_status(sid, "APPROVED")
    return {"status": "approved", "id": sid}

@bp.post("/admin/submissions/<int:sid>/reject")
@admin_required
def reject(sid: int):
    update_status(sid, "REJECTED")
    return {"status": "rejected", "id": sid}