#!/usr/bin/env bash
# ReviewBot AI — start backend (Linux/macOS)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "Copy .env.example to .env and add your API keys first."
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q
export PYTHONPATH="$ROOT"
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
