#!/usr/bin/env bash
# Start the dashboard locally on http://localhost:8000
#
#   ./run.sh                 # bundled SAMPLE data (works offline)
#   ILLNESS_LIVE=1 ./run.sh  # live data from CDC (needs internet)
set -euo pipefail

# Prefer the project venv's uvicorn if it exists.
if [ -x ".venv/bin/uvicorn" ]; then
  exec .venv/bin/uvicorn app.main:app --reload --port 8000
else
  exec uvicorn app.main:app --reload --port 8000
fi
