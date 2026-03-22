# 🎌 Anime AI Organizer Pro

**Organizador inteligente de imágenes de anime con IA avanzada y interfaz moderna**

Este proyecto es una aplicación completa para organizar automáticamente colecciones de imágenes de anime usando modelos de inteligencia artificial de última generación. Combina procesamiento de datos, reconocimiento de imágenes con IA, integración con APIs externas y una interfaz gráfica moderna para una experiencia de usuario excepcional.

---

## ✨ Características Principales

### 🤖 **Inteligencia Artificial Avanzada**
- **Modelos CLIP y YOLO** para reconocimiento preciso de anime en imágenes
- **Detección de personajes** con umbrales de confianza configurables
- **Embeddings y búsqueda semántica** usando FAISS para matching eficiente
- **Procesamiento batch** para máxima velocidad y rendimiento

### 🗄️ **Base de Datos Inteligente**
- **SQLite con estructura optimizada** - todas las tablas en MAYÚSCULA
- **Integración con MyAnimeList (MAL) API** - incluye sinopsis, rating, episodios, etc.
- **Nombres estandarizados** - conversión automática a mayúscula- **Filtrado inteligente** - solo crea carpetas de **ANIMES_VISTOS**- **Columnas enriquecidas**: título, rating, episodios, temporada, año, géneros, sinopsis

### 🎨 **Interfaz Gráfica Moderna**
- **PySide6 (Qt)** - interfaz nativa y profesional
- **5 pestañas especializadas**:
  - ⚙️ **Configuración** - rutas, opciones y ejecución principal
  - 🔄 **Procesando** - progreso en tiempo real del análisis
  - 📊 **Resultados** - estadísticas interactivas por carpeta
  - ⏳ **Pendientes** - imágenes sin clasificar
  - 🔄 **Renombrar** - herramienta dedicada para reorganizar archivos
- **Scroll en todas las pestañas** para navegación fluida
- **Diseño con gradientes** y elementos visuales atractivos

### 🔧 **Funcionalidades Avanzadas**
- **Organización automática** - crea carpetas por anime y mueve imágenes
- **Renombrado inteligente** - "NOMBRE_ANIME # 1.jpg", "# 2.jpg", etc.
- **Detección de duplicados** y filtrado inteligente
- **Modos mover/copiar** con opciones flexibles
- **Logs detallados** y manejo robusto de errores

---

## 🚀 Inicio Rápido

### Opción 1: Interfaz Gráfica (Recomendado)
```bash
cd '/home/jecla2517/Escritorio/programacion/ordenar imagenes'
source anime_env/bin/activate
python3 'app anime/gui.py'
```

### Opción 2: Línea de Comandos
```bash
cd '/home/jecla2517/Escritorio/programacion/ordenar imagenes'
source anime_env/bin/activate
python3 'app anime/anime_organizer.py' --excel 'lista de animes actualización.xlsx' --images 'anime/' --output 'filtrar/'
```

### Opción 3: Script Automático
```bash
bash '/home/jecla2517/Escritorio/programacion/ordenar imagenes/ejecutar_organizador.sh'
```

---

## 📋 Requisitos del Sistema

- **Python 3.8+** (probado con 3.12)
- **Entorno virtual** recomendado (venv o conda)
- **Espacio en disco**: ~600MB para modelos de IA (primera ejecución)

### Dependencias Principales
```
pandas>=2.1,<4
torch
open_clip_torch
faiss-cpu
ultralytics
pillow
opencv-python
pyside6
requests
sqlite3
```

### Instalación Automática
```bash
cd '/home/jecla2517/Escritorio/programacion/ordenar imagenes'
python3 'app anime/install_env.py'
```

---

## 🎯 Cómo Funciona

### 1. 📊 Preparación de Datos
- **Lectura del Excel**: Carga la lista de animes desde hoja de cálculo
- **Enriquecimiento con MAL API**: Obtiene metadatos adicionales (sinopsis, rating, etc.)
- **Creación de Base de Datos**: Almacena todo en SQLite con estructura optimizada
- **Limpieza Automática**: Elimina carpetas no válidas y devuelve imágenes a origen

### 2. 🧠 Análisis con IA Mejorado
- **Carga de Modelos**: CLIP para reconocimiento semántico, YOLO para detección
- **Procesamiento de Imágenes**: Análisis batch para máxima eficiencia
- **Algoritmo de Matching Multi-Nivel**:
  - **Learning**: Asignaciones aprendidas manualmente (100% confianza)
  - **Name Parts**: Matching por palabras clave con normalización inteligente (70%+ confianza)
  - **Exact Match**: Coincidencia exacta después de normalización (100% confianza)
  - **Similarity**: Búsqueda semántica por embeddings FAISS (75%+ confianza)
  - **IA Fallback**: CLIP como último recurso para casos difíciles (80%+ confianza)
- **Normalización Inteligente**: Preserva información clave, menos agresiva
- **Base de Datos Filtrada**: Solo usa títulos de la tabla **ANIMES_VISTOS**

### 3. 📁 Organización Automática
- **Limpieza Previa**: Elimina carpetas no válidas y devuelve imágenes al origen
- **Creación de Carpetas**: Una por cada anime, nombradas en MAYÚSCULA
- **Filtrado por Estado**: Solo crea carpetas de animes **VISTOS**
- **Movimiento de Imágenes**: Traslada archivos a sus carpetas correspondientes
- **Renombrado Estandarizado**: "NOMBRE_ANIME # 1.jpg", "# 2.jpg", etc.

### 4. 🔄 Renombrado Posterior (Proceso Independiente)
- **Herramienta separada**: `rename_tool.py` para renombrado independiente
- **Ejecución autónoma**: No requiere el proceso de organización
- **Reorganización**: Corrige nombres según base de datos actualizada
- **Estandarización**: Asegura consistencia en toda la colección

---

## 🎨 Interfaz Gráfica Detallada

### ⚙️ Pestaña Configuración
- **Rutas configurables**: Excel, imágenes de entrada, carpeta de salida
- **Opciones avanzadas**: Modo IA prioritario, umbrales de confianza
- **Botón principal**: "🚀 ¡INICIAR ORGANIZACIÓN!"
- **Barra de progreso**: Seguimiento en tiempo real

### 🔄 Pestaña Procesando
- **Lista en tiempo real**: Cada operación se registra aquí
- **Progreso visual**: Barra de progreso y estado actual
- **Logs detallados**: Información completa del proceso

### 📊 Pestaña Resultados
- **Estadísticas por carpeta**: Número de imágenes organizadas
- **Interfaz interactiva**: Click en carpeta muestra sus imágenes
- **Vista detallada**: Nombres de archivos individuales

### ⏳ Pestaña Pendientes
- **Imágenes sin clasificar**: Aquellas que no pudieron organizarse
- **Análisis detallado**: Razones del fallo y sugerencias
- **Opciones de corrección**: Posibilidad de reclasificación manual

### 🔄 Pestaña Renombrar
- **Herramienta especializada**: Para reorganizar colecciones existentes
- **Configuración dedicada**: Carpeta específica para renombrar
- **Información completa**: Explicación detallada de la funcionalidad
- **Progreso independiente**: Seguimiento específico del renombrado

---

## 🛠️ Uso Avanzado

### Opciones de Línea de Comandos
```bash
python3 anime_organizer.py [opciones]

Opciones principales:
  --excel RUTA          Archivo Excel con lista de animes
  --images RUTA         Carpeta con imágenes a organizar
  --output RUTA         Carpeta donde crear la organización
  --modo {mover,copiar} Modo de operación (por defecto: mover)
  --ai-first            Modo experimental: IA como primer método (no recomendado)
  --verbose             Salida detallada para depuración
  --help               Muestra todas las opciones disponibles
```

### Base de Datos
- **Ubicación**: `animes.db` en el directorio de salida
- **Estructura**: Una tabla por columna del Excel
- **Contenido**: Títulos en mayúscula + metadatos MAL
- **Campos**: title, rating, episodes, season, year, genres, synopsis

### Modelos de IA
- **CLIP**: Reconocimiento semántico de imágenes
- **YOLO**: Detección de personajes y elementos
- **FAISS**: Búsqueda eficiente de similitudes
- **Primera ejecución**: Descarga automática (~600MB)

---

## 🔧 Instalación y Configuración

### Entorno Virtual
```bash
# Crear entorno
python3 -m venv anime_env

# Activar entorno
source anime_env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Base de Datos Inicial
```bash
# Ejecutar script de creación
bash db_create.sh
```

### Modelos de IA
```bash
# Login opcional para acelerar descargas
huggingface-cli login

# Los modelos se descargan automáticamente en la primera ejecución
```

---

## 📊 Estructura del Proyecto

```
app anime/
├── ai_models.py          # Modelos de IA (CLIP, YOLO)
├── anime_organizer.py    # Lógica principal de organización
├── character_detector.py # Detección de personajes
├── config.py            # Configuraciones del sistema
├── filter_utils.py      # Utilidades de filtrado
├── gui.py               # Interfaz gráfica PySide6
├── gui_app.py           # Versión alternativa de GUI
├── mal_api.py           # Integración con MyAnimeList API
├── organizer_core.py    # Núcleo del organizador
├── rename_tool.py       # Herramienta independiente de renombrado
├── pyproject.toml       # Configuración del proyecto
├── README.md            # Esta documentación
├── requirements.txt     # Dependencias Python
├── setup_and_run.py     # Script de instalación
├── vector_index.py      # Índice vectorial FAISS
├── animes_database.py   # Creación de base de datos
└── __pycache__/         # Archivos compilados
```

---

## 🐛 Solución de Problemas

### Problemas Comunes
- **Modelo no descarga**: Verificar conexión a internet y espacio en disco
- **Error de rutas**: Usar rutas absolutas o relativas al directorio raíz
- **Memoria insuficiente**: Reducir batch size en configuraciones grandes
- **Base de datos corrupta**: Eliminar `animes.db` y recrear

### Logs y Depuración
- **Archivo de log**: `anime_organizer.log` en directorio de salida
- **Modo verbose**: Añadir `--verbose` para más información
- **Debug en GUI**: Ver pestaña "Procesando" para detalles en tiempo real

### Rendimiento
- **Primera ejecución**: Más lenta debido a descarga de modelos
- **Optimización**: Los modelos se cargan una sola vez por sesión
- **Batch processing**: Procesamiento en lotes para mejor rendimiento

---

## 🤝 Contribución

### Desarrollo
1. **Fork** el repositorio
2. **Crear rama** para nueva funcionalidad
3. **Commits** descriptivos siguiendo convenciones
4. **Pull Request** con descripción detallada

### Pruebas
```bash
# Ejecutar suite de pruebas
pytest tests/

# Pruebas específicas
pytest tests/test_anime.py::test_excel_reading
```

### Estándares de Código
- **PEP 8** para estilo Python
- **Docstrings** completas en funciones
- **Comentarios** explicativos en lógica compleja
- **Manejo de errores** robusto

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para detalles.

---

## 🙏 Agradecimientos

- **OpenAI CLIP** - Por el modelo de reconocimiento de imágenes
- **Ultralytics YOLO** - Por la detección de objetos
- **Meta FAISS** - Por la búsqueda vectorial eficiente
- **MyAnimeList** - Por la API de metadatos de anime
- **PySide6/Qt** - Por el framework de interfaz gráfica

---

## 📞 Soporte

Para soporte técnico o reportar bugs:
1. Revisar la sección de solución de problemas
2. Verificar logs en `anime_organizer.log`
3. Abrir issue en el repositorio con:
   - Descripción detallada del problema
   - Pasos para reproducir
   - Logs relevantes
   - Información del sistema

---

**¡Disfruta organizando tu colección de anime con IA! 🎌✨**
  ```
  O deja que la app lo solicite automáticamente la primera vez.
- Si tienes problemas de red o la descarga es muy lenta, puedes descargar manualmente el modelo desde [Hugging Face](https://huggingface.co/openai/clip-vit-base-patch32) y colocarlo en `~/.cache/open_clip`.
- Si la app se queda bloqueada descargando el modelo, verifica tu conexión o descarga el modelo manualmente.
- La GUI mostrará el progreso de la descarga del modelo si es necesario.

¡Disfruta organizando tus animes!

- Integración con MyAnimeList: al crear la base de datos, se consulta la API de MAL para cada anime y se agregan automáticamente las columnas de calificación, temporada, episodios y géneros.
- Es necesario un MAL_CLIENT_ID (ver https://myanimelist.net/apiconfig). Si no lo tienes, la app te lo pedirá la primera vez.
