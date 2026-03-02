from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.db import fetchone, execute

def create_user(username: str, password: str, role: str = "USER"):
    password_hash = generate_password_hash(password)
    execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, %s)
        """,
        (username, password_hash, role),
    )

def get_user_by_username(username: str):
    return fetchone("SELECT * FROM users WHERE username=%s", (username,))

def verify_password(user_row, password: str) -> bool:
    return check_password_hash(user_row["password_hash"], password)