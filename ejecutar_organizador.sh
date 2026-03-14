#!/bin/bash
# Script maestro para organizador de anime - Linux
cd "$(dirname "$0")"
if [ ! -f "run.sh" ]; then
    echo "Instalando dependencias..."
    python3 "app anime/install_env.py"
fi
bash start.sh

