"""
Benchmark du pipeline d'exécution PET_Projet
Mesure : overhead Docker, temps d'exécution, latence DB poll
"""
import time
import os
import psycopg2
import psycopg2.extras
import statistics
import tempfile
import shutil

# ── Config ──────────────────────────────────────────────────────────────────
DB = dict(host="localhost", port=5433, database="petdb", user="petuser", password="petpass")
STORAGE_HOST = r"C:\Users\User\Desktop\PET_Projet\storage\submissions"
STORAGE_CONTAINER = "/app/storage/submissions"
USER_ID = 1  # abdel

SCRIPTS = {
    "trivial": 'print("hello benchmark")',

    "calcul_cpu": """\
result = sum(i*i for i in range(1_000_000))
print(f"Sum: {result}")
""",

    "numpy_pandas": """\
import numpy as np
import pandas as pd
arr = np.random.rand(1000, 1000)
df = pd.DataFrame(arr)
print(f"Mean: {df.values.mean():.6f}")
print(f"Std:  {df.values.std():.6f}")
""",

    "matplotlib": """\
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
x = np.linspace(0, 10, 500)
plt.plot(x, np.sin(x))
plt.savefig('/tmp/plot.png')
print("Plot generated OK")
""",

    "scikit_learn": """\
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
X, y = make_classification(n_samples=500, n_features=20, random_state=42)
clf = RandomForestClassifier(n_estimators=50, random_state=42)
scores = cross_val_score(clf, X, y, cv=3)
print(f"CV accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")
""",
}

POLL_INTERVAL = 0.5   # secondes entre chaque poll
TIMEOUT       = 90    # secondes max par script


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_db():
    return psycopg2.connect(**DB, cursor_factory=psycopg2.extras.DictCursor)


def insert_submission(conn, name, script_code):
    """Écrit le fichier et insère la soumission en statut APPROVED."""
    os.makedirs(STORAGE_HOST, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"bench_user{USER_ID}_{ts}_{name}.py"
    host_path = os.path.join(STORAGE_HOST, filename)
    container_path = f"{STORAGE_CONTAINER}/{filename}"

    with open(host_path, "w", encoding="utf-8") as f:
        f.write(script_code)

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO submissions (user_id, name, file_path, status, created_at, updated_at)
           VALUES (%s, %s, %s, 'APPROVED', NOW(), NOW()) RETURNING id""",
        (USER_ID, name, container_path),
    )
    sid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return sid, host_path


def wait_for_result(conn, sid):
    """Poll jusqu'à FINISHED/FAILED, retourne (status, stdout, stderr, elapsed)."""
    start = time.perf_counter()
    while True:
        elapsed = time.perf_counter() - start
        if elapsed > TIMEOUT:
            return "TIMEOUT", "", "", elapsed

        cur = conn.cursor()
        cur.execute("SELECT status, stdout, stderr FROM submissions WHERE id=%s", (sid,))
        row = cur.fetchone()
        cur.close()

        if row and row["status"] in ("FINISHED", "FAILED"):
            return row["status"], row["stdout"] or "", row["stderr"] or "", elapsed

        time.sleep(POLL_INTERVAL)


def cleanup(conn, sid, host_path):
    cur = conn.cursor()
    cur.execute("DELETE FROM submissions WHERE id=%s", (sid,))
    conn.commit()
    cur.close()
    try:
        os.remove(host_path)
    except FileNotFoundError:
        pass


# ── Benchmark ─────────────────────────────────────────────────────────────────
def run_benchmark(runs=3):
    print("=" * 60)
    print("  BENCHMARK PET_Projet - Pipeline execution sandbox")
    print("=" * 60)
    print(f"  DB       : localhost:{DB['port']}")
    print(f"  Runs     : {runs} par script")
    print(f"  Poll     : {POLL_INTERVAL}s | Timeout : {TIMEOUT}s")
    print("=" * 60)

    conn = get_db()
    all_results = {}

    for script_name, code in SCRIPTS.items():
        print(f"\n[ {script_name} ]")
        timings = []
        statuses = []

        for i in range(runs):
            sid, host_path = insert_submission(conn, f"{script_name}_r{i}", code)
            status, stdout, stderr, elapsed = wait_for_result(conn, sid)
            cleanup(conn, sid, host_path)

            timings.append(elapsed)
            statuses.append(status)
            mark = "OK" if status == "FINISHED" else status
            print(f"  run {i+1}/{runs} : {elapsed:6.2f}s  [{mark}]")
            if status == "FAILED":
                print(f"    stderr: {stderr[:120]}")

        all_results[script_name] = timings

        if len(timings) > 1:
            print(f"  >> min={min(timings):.2f}s  max={max(timings):.2f}s  "
                  f"avg={statistics.mean(timings):.2f}s  "
                  f"stdev={statistics.stdev(timings):.2f}s")
        else:
            print(f"  >> {timings[0]:.2f}s")

    conn.close()

    # ── Résumé final ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RÉSUMÉ")
    print("=" * 60)
    print(f"  {'Script':<20} {'min':>6} {'avg':>6} {'max':>6}  stdev")
    print(f"  {'-'*50}")
    for name, t in all_results.items():
        avg = statistics.mean(t)
        print(f"  {name:<20} {min(t):>5.2f}s {avg:>5.2f}s {max(t):>5.2f}s  "
              f"±{statistics.stdev(t) if len(t)>1 else 0:.2f}s")

    baseline = statistics.mean(all_results["trivial"])
    print(f"\n  Overhead Docker (baseline trivial) : ~{baseline:.2f}s"
          .encode("ascii", "replace").decode("ascii"))
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark(runs=3)
