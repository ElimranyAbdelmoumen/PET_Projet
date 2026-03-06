import os
import time
import subprocess
import psycopg2

DB_HOST = os.environ.get("POSTGRES_HOST", "db")
DB_NAME = os.environ.get("POSTGRES_DB", "petdb")
DB_USER = os.environ.get("POSTGRES_USER", "petuser")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "petpass")

STORAGE_PATH = "/storage"
HOST_STORAGE_PATH = os.environ.get("HOST_STORAGE_PATH", "/storage")


def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def execute_script(file_path):
    local_path = file_path.replace("/app/storage", STORAGE_PATH)
    host_path = file_path.replace("/app/storage", HOST_STORAGE_PATH)

    if not os.path.exists(local_path):
        return "", f"File not found: {local_path}", -1

    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "256m",
        "--cpus", "0.5",
        "-v", f"{host_path}:/work/script.py:ro",
        "portwatch-python-runner:1.0",
        "/work/script.py"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        return result.stdout, result.stderr, result.returncode

    except subprocess.TimeoutExpired:
        return "", "Execution timeout", -1


def worker_loop():

    while True:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        SELECT id,file_path
        FROM submissions
        WHERE status='APPROVED'
        LIMIT 1
        """)

        row = cur.fetchone()

        if row:

            submission_id,file_path = row

            stdout,stderr,code = execute_script(file_path)

            status = "FINISHED" if code == 0 else "FAILED"

            cur.execute("""
            UPDATE submissions
            SET status=%s,
                stdout=%s,
                stderr=%s,
                exit_code=%s,
                updated_at=NOW()
            WHERE id=%s
            """,(status,stdout,stderr,code,submission_id))

            conn.commit()

            print("Executed submission",submission_id)

        cur.close()
        conn.close()

        time.sleep(3)


if __name__ == "__main__":
    worker_loop()