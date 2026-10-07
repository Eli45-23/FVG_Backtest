#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv work/.venv
work/.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci)
echo 'Installed. Start with ./run_app.sh'
