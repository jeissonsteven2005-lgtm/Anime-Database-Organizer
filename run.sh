#!/bin/bash
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Si no hay entorno virtual, crear e instalar dependencias
if [ ! -d "$ROOT/.venv" ]; then
  echo "Entorno virtual no encontrado (.venv). Instalando dependencias..."
  python3 "app anime/install_env.py"
fi

# Asegurarse de que pandas esté disponible (comprobación rápida de dependencias)
if ! "$ROOT/.venv/bin/python" -c "import pandas" >/dev/null 2>&1; then
  echo "Instalando dependencias de Python faltantes..."
  "$ROOT/.venv/bin/pip" install -r "app anime/requirements.txt"
fi

source "$ROOT/.venv/bin/activate"
python3 "app anime/gui.py"
