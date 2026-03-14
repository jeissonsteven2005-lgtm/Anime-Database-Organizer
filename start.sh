#!/bin/bash

# Script maestro para iniciar el organizador de anime
cd "/home/jecla2517/Escritorio/programacion/ordenar imagenes"
PROJECT_PATH="$(pwd)"
INSTALL_ENV='app anime/install_env.py'
RUN_SH='run.sh'

# Si run.sh no existe, ejecutar instalación primero
if [ ! -f "$RUN_SH" ]; then
    echo "Instalando dependencias..."
    python3 "$INSTALL_ENV"
fi

# Ejecutar la app
echo "Iniciando organizador de anime..."
bash "$RUN_SH"

