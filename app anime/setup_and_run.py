#!/usr/bin/env python3
import os
import subprocess
import sys

# Paths corregidos
PROJECT_ROOT = "/home/jecla2517/Escritorio/programacion/ordenar imagenes"
APP_DIR = os.path.join(PROJECT_ROOT, "app anime")

# Prefer a standard .venv directory, but keep backwards compatibility with anime_env
VENV_CANDIDATES = [os.path.join(PROJECT_ROOT, ".venv"), os.path.join(PROJECT_ROOT, "anime_env")]
VENV_DIR = next((p for p in VENV_CANDIDATES if os.path.isdir(p)), VENV_CANDIDATES[0])

DESKTOP_DIR = os.path.expanduser("~/Escritorio")
GUI_SCRIPT = os.path.join(APP_DIR, "gui.py")
REQUIREMENTS = os.path.join(APP_DIR, "requirements.txt")

def run(cmd, env=None):
    """Ejecuta un comando y lanza excepción si falla."""
    print("Ejecutando: %s" % (" ".join(cmd) if isinstance(cmd, list) else cmd))
    subprocess.run(cmd, check=True, env=env)

def create_venv():
    if not os.path.isdir(VENV_DIR):
        print("Creando entorno virtual...")
        run([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print("Entorno virtual ya existe, omitiendo creación.")

def install_packages():
    pip_path = os.path.join(VENV_DIR, "bin", "pip")
    print("Actualizando pip...")
    run([pip_path, "install", "--upgrade", "pip"])
    
    if os.path.isfile(REQUIREMENTS):
        print("Instalando dependencias desde requirements.txt...")
        run([pip_path, "install", "-r", REQUIREMENTS])
    else:
        print("No se encontró requirements.txt. Instala manualmente.")

def create_desktop_shortcut():
    shortcut_path = os.path.join(DESKTOP_DIR, "Anime_Organizer.desktop")
    print("Creando acceso directo en %s..." % shortcut_path)
    python_path = os.path.join(VENV_DIR, "bin", "python3")
    content = """[Desktop Entry]
Type=Application
Name=Anime Organizer
Exec=%s %s
Terminal=true
Icon=applications-multimedia
""" % (python_path, GUI_SCRIPT)
    with open(shortcut_path, "w") as f:
        f.write(content)
    os.chmod(shortcut_path, 0o755)
    print("Acceso directo creado: %s" % shortcut_path)

def run_gui():
    python_path = os.path.join(VENV_DIR, "bin", "python3")
    print("Abriendo GUI...")
    run([python_path, GUI_SCRIPT])

def main():
    print("=== Setup y Run Anime Organizer ===")
    create_venv()
    install_packages()
    create_desktop_shortcut()
    run_gui()

if __name__ == "__main__":
    main()

