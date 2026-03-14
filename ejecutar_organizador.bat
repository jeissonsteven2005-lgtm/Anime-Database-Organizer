@echo off
REM Script maestro para organizador de anime - Windows
cd /d "%~dp0"
if not exist run.bat (
    echo Instalando dependencias...
    python "app anime\install_env.py"
)
call anime_env\Scripts\activate.bat
call run.bat
pause

