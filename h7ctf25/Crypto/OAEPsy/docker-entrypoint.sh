#!/usr/bin/env bash
set -euo pipefail

UUID=$(python - <<'PY'
import uuid, sys
print(uuid.uuid4())
PY
)

cat > /app/secret.py <<PY
FLAG = b"H7CTF{https://archiv.infsec.ethz.ch/education/fs08/secsem/manger01.pdf-${UUID}}"
PY

exec "$@"
