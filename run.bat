@echo off
REM Ejecuta el organizador de anime (Windows)
setlocal

cd /d "%~dp0"

REM Preferir .venv, crear si no existe
if not exist ".venv\Scripts\activate.bat" (
  echo Creando entorno virtual (.venv)...
  python -m venv ".venv"
  call ".venv\Scripts\activate.bat"
  echo Instalando dependencias...
  pip install --upgrade pip
  pip install -r "app anime\requirements.txt"
) else (
  call ".venv\Scripts\activate.bat"
  python -c "import pandas" 2>nul || (
    echo Instalando dependencias (faltantes)...
    pip install -r "app anime\requirements.txt"
  )
)

python "app anime\gui.py"
endlocal
