#!/usr/bin/env python3

import os
import subprocess
import sys

# Ruta del proyecto
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_NAME = os.path.join(PROJECT_PATH, "anime_env")

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
    """Script run.sh."""
    script = f'''#!/bin/bash
source "{VENV_NAME}/bin/activate"
cd "{PROJECT_PATH}"
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

