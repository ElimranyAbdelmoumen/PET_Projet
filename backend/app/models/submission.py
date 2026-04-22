from app.utils.db import execute, fetchall, fetchone


def create_submission(user_id: int, file_path: str, name: str = None, microdata_guid: str = None):
    row = fetchone(
        """
        INSERT INTO submissions (user_id, name, file_path, microdata_guid, status)
        VALUES (%s, %s, %s, %s, 'PENDING')
        RETURNING id, status, name
        """,
        (user_id, name, file_path, microdata_guid),
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
        SELECT s.id, s.user_id, u.username, s.name, s.file_path, s.microdata_guid,
               s.status, s.stdout, s.stderr, s.exit_code, s.created_at
        FROM submissions s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.id DESC
        """
    )


def get_submission_by_id(submission_id: int):
    return fetchone(
        """
        SELECT s.id, s.user_id, u.username, s.name, s.file_path, s.microdata_guid,
               s.status, s.stdout, s.stderr, s.exit_code, s.created_at
        FROM submissions s
        JOIN users u ON u.id = s.user_id
        WHERE s.id = %s
        """,
        (submission_id,),
    )


def list_user_submissions(user_id: int, search: str = None):
    if search:
        return fetchall(
            """
            SELECT id, name, file_path, status, stdout, stderr, exit_code, created_at
            FROM submissions
            WHERE user_id = %s AND name ILIKE %s
            ORDER BY id DESC
            """,
            (user_id, f"%{search}%"),
        )
    return fetchall(
        """
        SELECT id, name, file_path, status, stdout, stderr, exit_code, created_at
        FROM submissions
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,),
    )


def get_user_submission(user_id: int, submission_id: int):
    return fetchone(
        """
        SELECT id, name, file_path, status, stdout, stderr, exit_code, created_at
        FROM submissions
        WHERE id = %s AND user_id = %s
        """,
        (submission_id, user_id),
    )


def update_status(submission_id: int, status: str):
    execute(
        "UPDATE submissions SET status=%s, updated_at=NOW() WHERE id=%s",
        (status, submission_id),
    )