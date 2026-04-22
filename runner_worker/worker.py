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
CONTAINER_OUTPUTS_BASE = "/app/storage/outputs"


def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def execute_script(file_path, microdata_file_path=None, outputs_dir=None, local_outputs_dir=None):
    local_path = file_path.replace("/app/storage", STORAGE_PATH)
    host_path = file_path.replace("/app/storage", HOST_STORAGE_PATH)

    if not os.path.exists(local_path):
        return "", f"File not found: {local_path}", -1

    ext = os.path.splitext(file_path)[1].lower() or ".py"
    container_script = f"/work/script{ext}"

    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1.0",
        "-v", f"{host_path}:{container_script}:ro",
    ]

    if microdata_file_path:
        host_data = microdata_file_path.replace("/app/storage", HOST_STORAGE_PATH)
        data_filename = os.path.basename(microdata_file_path)
        cmd += ["-v", f"{host_data}:/work/data/{data_filename}:ro"]

    if outputs_dir:
        os.makedirs(local_outputs_dir or outputs_dir, exist_ok=True)
        cmd += ["-v", f"{outputs_dir}:/work/outputs"]

    cmd += ["portwatch-python-runner:1.0", container_script]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        stdout = result.stdout
        output_section = ""

        if "===OUTPUTS===" in stdout:
            parts = stdout.split("===OUTPUTS===")
            stdout = parts[0].replace("===STDOUT===", "").strip()
            output_section = parts[1].strip() if len(parts) > 1 else ""
        else:
            stdout = stdout.replace("===STDOUT===", "").strip()

        full_output = stdout
        if output_section:
            full_output += "\n\n=== Resultats Python ===\n" + output_section

        return full_output, result.stderr, result.returncode

    except subprocess.TimeoutExpired:
        return "", "Execution timeout (60s max)", -1


def collect_outputs(submission_id, local_outputs_dir, conn):
    if not local_outputs_dir or not os.path.isdir(local_outputs_dir):
        return False

    files = [f for f in os.listdir(local_outputs_dir)
             if os.path.isfile(os.path.join(local_outputs_dir, f))]
    if not files:
        return False

    cur = conn.cursor()
    for filename in files:
        container_path = f"{CONTAINER_OUTPUTS_BASE}/{submission_id}/{filename}"
        cur.execute(
            "INSERT INTO submission_outputs (submission_id, filename, file_path) VALUES (%s, %s, %s)",
            (submission_id, filename, container_path),
        )
    cur.close()
    return True


def worker_loop():

    while True:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        SELECT s.id, s.file_path, m.file_path AS microdata_file_path
        FROM submissions s
        LEFT JOIN microdata_files m ON m.guid = s.microdata_guid
        WHERE s.status='APPROVED'
        LIMIT 1
        """)

        row = cur.fetchone()

        if row:

            submission_id, file_path, microdata_file_path = row

            host_outputs_dir = os.path.join(HOST_STORAGE_PATH, "outputs", str(submission_id))
            local_outputs_dir = os.path.join(STORAGE_PATH, "outputs", str(submission_id))

            stdout, stderr, code = execute_script(
                file_path, microdata_file_path,
                outputs_dir=host_outputs_dir, local_outputs_dir=local_outputs_dir
            )

            status = "FINISHED" if code == 0 else "FAILED"

            has_outputs = collect_outputs(submission_id, local_outputs_dir, conn)
            outputs_status = "PENDING_VALIDATION" if has_outputs else "NONE"

            cur.execute("""
            UPDATE submissions
            SET status=%s,
                outputs_status=%s,
                stdout=%s,
                stderr=%s,
                exit_code=%s,
                updated_at=NOW()
            WHERE id=%s
            """, (status, outputs_status, stdout, stderr, code, submission_id))

            conn.commit()

            print("Executed submission", submission_id)

        cur.close()
        conn.close()

        time.sleep(3)


if __name__ == "__main__":
    worker_loop()
