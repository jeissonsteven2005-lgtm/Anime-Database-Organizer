if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en setup_and_run.py:\n{e}\n\n{traceback.format_exc()}")
#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

# Rutas base (ajustadas a tu proyecto sin espacios)
BASE_DIR = os.path.expanduser("~/Escritorio/programacion/ordenar_imagenes/app_anime")
VENV_DIR = os.path.join(BASE_DIR, "anime_env")
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
GUI_SCRIPT = os.path.join(BASE_DIR, "gui.py")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")


def run(cmd, env=None):
    """Ejecuta un comando y lanza excepción si falla."""
    print(f"Ejecutando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
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
        print("No se encontró requirements.txt. Puedes instalar paquetes manualmente.")


def create_desktop_shortcut():
    shortcut_path = os.path.join(DESKTOP_DIR, "Anime Organizer.desktop")
    print(f"Creando acceso directo en {shortcut_path}...")
    content = f"""[Desktop Entry]
Type=Application
Name=Anime Organizer
Exec={os.path.join(VENV_DIR, "bin", "python3")} {GUI_SCRIPT}
Terminal=true
"""
    with open(shortcut_path, "w") as f:
        f.write(content)
    os.chmod(shortcut_path, 0o755)


def run_gui():
    python_path = os.path.join(VENV_DIR, "bin", "python3")
    print("Abriendo GUI...")
    run([python_path, GUI_SCRIPT])


def main():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(DESKTOP_DIR, exist_ok=True)

    create_venv()
    install_packages()
    create_desktop_shortcut()
    run_gui()


if __name__ == "__main__":
    main()