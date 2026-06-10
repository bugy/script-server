#!/usr/bin/env bash
# Starts the script-server backend with a fully isolated configuration for the
# Playwright e2e suite. It NEVER reads or writes the developer's real conf/.
#
# - config dir : web-src/tests/e2e/fixtures/conf (port 5099, cookie_secure=false,
#                XSRF token mode kept ON so the real browser flow is exercised)
# - logs/temp  : web-src/tests/e2e/.run/ (gitignored)
# - python deps: a dedicated .e2e_venv at the project root, created on demand
set -euo pipefail

cd "$(dirname "$0")/../../.."  # project root

PY=.e2e_venv/bin/python
if [ ! -x "$PY" ]; then
    echo "[e2e] creating .e2e_venv and installing backend deps..."
    python3 -m venv .e2e_venv
    .e2e_venv/bin/pip install -q -r requirements.txt
fi

mkdir -p web-src/tests/e2e/.run/logs web-src/tests/e2e/.run/temp

exec "$PY" launcher.py \
    -d web-src/tests/e2e/fixtures/conf \
    -l web-src/tests/e2e/.run/logs \
    -t web-src/tests/e2e/.run/temp
