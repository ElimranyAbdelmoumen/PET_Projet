#!/usr/bin/env bash
# Benchmark PET sandbox - mesure le temps d'exécution réel du conteneur Docker
# Usage: bash benchmark/run_benchmarks.sh

HOST_STORAGE="c:/Users/User/Desktop/PET_Projet/storage"
RUNNER_IMAGE="portwatch-python-runner:1.0"
RESULTS_FILE="benchmark/results.txt"

mkdir -p benchmark/scripts benchmark/outputs
> "$RESULTS_FILE"

log() { echo "$@" | tee -a "$RESULTS_FILE"; }

run_bench() {
  local label="$1"
  local script="$2"
  local extra_args="${3:-}"
  local N=5

  log ""
  log "=== $label (N=$N runs) ==="
  local total=0
  for i in $(seq 1 $N); do
    local start=$(date +%s%3N)
    docker run --rm --network none --memory 512m --cpus 1.0 \
      -v "$script:/work/script${script##*.script}:ro" \
      $extra_args \
      "$RUNNER_IMAGE" "/work/script${script##*.script}" > /dev/null 2>&1
    local end=$(date +%s%3N)
    local elapsed=$((end - start))
    log "  run $i: ${elapsed}ms"
    total=$((total + elapsed))
  done
  local avg=$((total / N))
  log "  moyenne: ${avg}ms"
}

# ─── Scripts de test ────────────────────────────────────────────────────────

cat > benchmark/scripts/hello.py << 'EOF'
print("hello")
EOF

cat > benchmark/scripts/pandas_basic.py << 'EOF'
import pandas as pd
import numpy as np
df = pd.DataFrame({'x': range(1000), 'y': np.random.rand(1000)})
result = df.describe()
print(result)
EOF

cat > benchmark/scripts/ml_basic.py << 'EOF'
import numpy as np
from sklearn.linear_model import LinearRegression
X = np.random.rand(500, 5)
y = np.random.rand(500)
model = LinearRegression().fit(X, y)
print("score:", model.score(X, y))
EOF

cat > benchmark/scripts/with_data.py << 'EOF'
import pandas as pd
df = pd.read_csv("/work/data/population_sample.csv")
print(df.describe())
print("rows:", len(df))
EOF

cat > benchmark/scripts/with_output.py << 'EOF'
import pandas as pd
import numpy as np
df = pd.DataFrame({'a': range(100), 'b': np.random.rand(100)})
df.to_csv("/work/outputs/bench_result.csv", index=False)
print("saved")
EOF

cat > benchmark/scripts/hello.r << 'EOF'
cat("hello from R\n")
EOF

cat > benchmark/scripts/stats_basic.r << 'EOF'
x <- rnorm(1000)
cat("mean:", mean(x), "\n")
cat("sd:", sd(x), "\n")
summary(x)
EOF

cat > benchmark/scripts/with_data.r << 'EOF'
df <- read.csv("/work/data/population_sample.csv")
cat("rows:", nrow(df), "\n")
print(summary(df))
EOF

# ─── Exécution ───────────────────────────────────────────────────────────────

SCRIPT_DIR="$(pwd)/benchmark/scripts"
DATA_FILE="$(pwd)/storage/microdata/population_sample.csv"
OUTPUT_DIR="$(pwd)/benchmark/outputs"
mkdir -p "$OUTPUT_DIR"

log "================================================"
log " BENCHMARK PET SANDBOX — $(date '+%Y-%m-%d %H:%M:%S')"
log "================================================"
log "Image : $RUNNER_IMAGE"
log "Limites : 512m RAM / 1 CPU / réseau désactivé"

# Python
log ""
log "──────────────────────────────────────────────"
log " PYTHON"
log "──────────────────────────────────────────────"

for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/hello.py:/work/script.py:ro" \
    "$RUNNER_IMAGE" /work/script.py > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES_PY_HELLO+=($((end-start)))
done
AVG=0; for t in "${TIMES_PY_HELLO[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES_PY_HELLO[@]}))
log ""
log "=== Python hello (N=5) ==="
log "  runs: ${TIMES_PY_HELLO[*]} ms"
log "  moyenne: ${AVG} ms"

TIMES=()
for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/pandas_basic.py:/work/script.py:ro" \
    "$RUNNER_IMAGE" /work/script.py > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== Python pandas describe (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

TIMES=()
for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/ml_basic.py:/work/script.py:ro" \
    "$RUNNER_IMAGE" /work/script.py > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== Python sklearn (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

TIMES=()
for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/with_data.py:/work/script.py:ro" \
    -v "$DATA_FILE:/work/data/population_sample.csv:ro" \
    "$RUNNER_IMAGE" /work/script.py > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== Python + microdata CSV (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

TIMES=()
for i in $(seq 1 5); do
  rm -f "$OUTPUT_DIR/bench_result.csv"
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/with_output.py:/work/script.py:ro" \
    -v "$OUTPUT_DIR:/work/outputs" \
    "$RUNNER_IMAGE" /work/script.py > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== Python + écriture output CSV (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

# R
log ""
log "──────────────────────────────────────────────"
log " R"
log "──────────────────────────────────────────────"

TIMES=()
for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/hello.r:/work/script.R:ro" \
    "$RUNNER_IMAGE" /work/script.R > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== R hello (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

TIMES=()
for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/stats_basic.r:/work/script.R:ro" \
    "$RUNNER_IMAGE" /work/script.R > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== R stats rnorm(1000) (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

TIMES=()
for i in $(seq 1 5); do
  start=$(date +%s%3N)
  docker run --rm --network none --memory 512m --cpus 1.0 \
    -v "$SCRIPT_DIR/with_data.r:/work/script.R:ro" \
    -v "$DATA_FILE:/work/data/population_sample.csv:ro" \
    "$RUNNER_IMAGE" /work/script.R > /dev/null 2>&1
  end=$(date +%s%3N)
  TIMES+=($((end-start)))
done
AVG=0; for t in "${TIMES[@]}"; do AVG=$((AVG+t)); done; AVG=$((AVG/${#TIMES[@]}))
log ""
log "=== R + microdata CSV (N=5) ==="
log "  runs: ${TIMES[*]} ms"
log "  moyenne: ${AVG} ms"

log ""
log "================================================"
log " FIN DU BENCHMARK"
log "================================================"
echo ""
echo "Résultats sauvegardés dans : $RESULTS_FILE"
