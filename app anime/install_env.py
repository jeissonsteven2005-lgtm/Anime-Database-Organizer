#!/usr/bin/env python3

import os
import subprocess
import sys

# Ruta del proyecto
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_VENV = os.path.join(PROJECT_PATH, ".venv")
LEGACY_VENV = os.path.join(PROJECT_PATH, "anime_env")


def get_venv_path():
    """Prefer standard .venv; fallback to anime_env for backwards compatibility."""
    if os.path.isdir(DEFAULT_VENV):
        return DEFAULT_VENV
    return LEGACY_VENV


# Venv path for this installation / execution
VENV_NAME = get_venv_path()

DEPENDENCIES = [
    "torch",
    "torchvision",
    "pandas",
    "Pillow",
    "open-clip-torch",
    "faiss-cpu",
    "PySide6",
    "opencv-python",
    "openpyxl"
]

def run(cmd):
    """Ejecuta comando shell."""
    print(f">>> {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def check_python():
    """Verifica Python 3.9+."""
    if sys.version_info < (3, 9):
        print("Requiere Python 3.9+")
        sys.exit(1)
    print("Python OK")

def install_system():
    """Paquetes Ubuntu."""
    run("sudo apt update")
    run("sudo apt install -y python3-venv python3-pip git build-essential libgl1 libglib2.0-0")

def create_venv():
    """Crea entorno virtual."""
    if os.path.exists(VENV_NAME):
        print("Venv existe")
        return
    run(f'"python3" -m venv "{VENV_NAME}"')
    print(f"Venv en {VENV_NAME}")

def install_deps():
    """Instala Python deps."""
    pip = os.path.join(VENV_NAME, "bin", "pip")
    run(f'"{pip}" install --upgrade pip')
    for dep in DEPENDENCIES:
        run(f'"{pip}" install "{dep}"')

def create_run():
    """Crea un wrapper run.sh que prepara el venv y ejecuta la GUI."""
    script = f'''#!/bin/bash
set -e

ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
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
'''
    run_sh = os.path.join(PROJECT_PATH, "run.sh")
    with open(run_sh, "w") as f:
        f.write(script)
    os.chmod(run_sh, 0o755)
    print(f"run.sh creado: {run_sh}")

if __name__ == "__main__":
    print("=== Anime Organizer Installer ===")
    check_python()
    install_system()
    create_venv()
    install_deps()
    create_run()
    print("\n¡Listo! Ejecuta: bash run.sh")

