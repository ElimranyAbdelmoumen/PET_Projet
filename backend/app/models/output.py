from app.utils.db import execute, fetchall, fetchone


def list_outputs(submission_id):
    return fetchall(
        "SELECT id, filename, file_path, created_at FROM submission_outputs WHERE submission_id=%s ORDER BY filename",
        (submission_id,)
    )


def get_output_by_filename(submission_id, filename):
    return fetchone(
        "SELECT id, filename, file_path FROM submission_outputs WHERE submission_id=%s AND filename=%s",
        (submission_id, filename)
    )


def get_pending_outputs_count():
    row = fetchone(
        "SELECT COUNT(*) AS n FROM submissions WHERE outputs_status='PENDING_VALIDATION'",
        ()
    )
    return row["n"] if row else 0


def approve_outputs(submission_id):
    execute(
        "UPDATE submissions SET outputs_status='APPROVED', updated_at=NOW() WHERE id=%s",
        (submission_id,)
    )


def reject_outputs(submission_id):
    execute(
        "UPDATE submissions SET outputs_status='REJECTED', updated_at=NOW() WHERE id=%s",
        (submission_id,)
    )
