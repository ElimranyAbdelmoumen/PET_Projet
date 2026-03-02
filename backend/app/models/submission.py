from app.utils.db import execute, fetchall, fetchone


def create_submission(user_id: int, file_path: str):
    row = fetchone(
        """
        INSERT INTO submissions (user_id, file_path, status)
        VALUES (%s, %s, 'PENDING')
        RETURNING id, status
        """,
        (user_id, file_path),
    )
    return row


def get_submission(submission_id: int):
    return fetchone(
        """
        SELECT id, status
        FROM submissions
        WHERE id = %s
        """,
        (submission_id,),
    )


def list_all_submissions():
    return fetchall(
        """
        SELECT s.id, s.user_id, u.username, s.file_path, s.status, s.created_at
        FROM submissions s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.id DESC
        """
    )


def update_status(submission_id: int, status: str):
    execute(
        "UPDATE submissions SET status=%s, updated_at=NOW() WHERE id=%s",
        (status, submission_id),
    )