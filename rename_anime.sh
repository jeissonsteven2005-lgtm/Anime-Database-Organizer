# Script para ejecutar el renombrado independiente de anime
# Uso: ./rename_anime.sh [carpeta_output] [archivo_excel]

# Mostrar ayuda si se solicita
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "🎌 Anime Renamer Tool - Script Independiente"
    echo "=============================================="
    echo ""
    echo "Uso:"
    echo "  ./rename_anime.sh [carpeta_output] [archivo_excel]"
    echo ""
    echo "Parámetros:"
    echo "  carpeta_output    Directorio a renombrar (por defecto: 'filtrar/')"
    echo "  archivo_excel     Archivo Excel específico (opcional)"
    echo ""
    echo "Ejemplos:"
    echo "  ./rename_anime.sh"
    echo "  ./rename_anime.sh filtrar/"
    echo "  ./rename_anime.sh filtrar/ lista.xlsx"
    echo ""
    exit 0
fi

echo "🎌 Anime Renamer Tool - Proceso Independiente"
echo "=============================================="

# Activar entorno virtual
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "anime_env/bin/activate" ]; then
    source anime_env/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️  Entorno virtual no encontrado, intentando con python3 del sistema"
fi

# Parámetros
OUTPUT_DIR=${1:-"filtrar/"}
EXCEL_FILE=${2:-""}

# Verificar que existe el directorio de salida
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ Error: Directorio de salida '$OUTPUT_DIR' no existe"
    exit 1
fi

echo "📁 Directorio a procesar: $OUTPUT_DIR"

# Construir comando
CMD="python3 'app anime/rename_tool.py' --output '$OUTPUT_DIR' --verbose"

if [ -n "$EXCEL_FILE" ] && [ -f "$EXCEL_FILE" ]; then
    CMD="$CMD --excel '$EXCEL_FILE'"
    echo "📊 Archivo Excel especificado: $EXCEL_FILE"
else
    echo "🔍 Buscando archivo Excel automáticamente..."
fi

echo "🚀 Ejecutando comando:"
echo "$CMD"
echo ""

# Ejecutar
eval "$CMD"

# Resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Renombrado completado exitosamente"
else
    echo ""
    echo "❌ Error durante el renombrado"
    exit 1
fi