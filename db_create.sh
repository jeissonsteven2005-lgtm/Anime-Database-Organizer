#!/bin/bash
# Crea DB y carpetas all desde Excel, usando el venv del proyecto
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
if [ ! -d "$VENV" ]; then
  VENV="$ROOT/anime_env"
fi

if [ -d "$VENV" ]; then
  source "$VENV/bin/activate"
else
  echo "No se encontró entorno virtual (.venv ni anime_env). Ejecuta: python3 'app anime/install_env.py'"
  exit 1
fi

cd "$ROOT"
python3 animes_database.py

