#!/bin/bash
# SessionStart hook for Claude Code on the web.
# Creates/refreshes the project's virtualenv and installs dependencies so that
# the tests (pytest) and the app (uvicorn) are ready the moment a session starts.
set -euo pipefail

# Only do work in remote (Claude Code on the web) sessions. Local development
# follows the manual setup in the README.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Repo root (fall back to this script's location if the env var is unset).
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR"

echo "[session-start] preparing Python environment..." >&2

# 1. Create the virtualenv once (idempotent; reused from cached container state).
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

# 2. Install/refresh dependencies.
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

# 3. Expose the venv tools and local imports for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"$PROJECT_DIR/.venv/bin:\$PATH\""
    echo "export PYTHONPATH=\"$PROJECT_DIR\""
  } >> "$CLAUDE_ENV_FILE"
fi

echo "[session-start] done: .venv ready, pytest and uvicorn available." >&2
