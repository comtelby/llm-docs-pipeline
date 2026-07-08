#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

source venv/bin/activate

# Если хочешь сразу веб-интерфейс
exec uvicorn app:app --host 0.0.0.0 --port 8000

# Или, если хочешь разовый отчёт без веб-интерфейса:
# exec python pipeline.py
