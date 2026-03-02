import os
from datetime import datetime
from flask import Blueprint, request, session
from app.utils.authz import login_required
from app.models.submission import create_submission

bp = Blueprint("submissions", __name__)

@bp.post("/submit")
@login_required
def submit():
    data = request.get_json(force=True)
    code = data.get("code", "")
    if not code.strip():
        return {"error": "code is required"}, 400

    user_id = session["user_id"]

    base_dir = "/app/storage/submissions"
    os.makedirs(base_dir, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"user{user_id}_{ts}.py"
    file_path = os.path.join(base_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    created = create_submission(user_id, file_path)
    return {"status": "submitted", "submission": created}, 201