@echo off
REM Script maestro para organizador de anime - Windows
cd /d "%~dp0"

REM Ejecuta el script principal (run.bat) que se encarga de crear el venv e instalar dependencias si falta algo.
call run.bat
pause

