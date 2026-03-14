# Organizador de Anime (Mejorado con IA)

Este proyecto es una utilidad avanzada en Python para organizar imágenes de anime usando inteligencia artificial. Ahora incluye:


1. Lectura de hojas de cálculo (Excel/CSV) con títulos de anime.
2. Almacenamiento en base de datos SQLite (todas las tablas en mayúsculas y ordenadas alfabéticamente).
3. Organización automática de imágenes en carpetas por anime usando modelos de IA (CLIP y YOLO).
4. Detección de personajes en imágenes con umbral de confianza y nombres de clase.
5. Búsqueda y comparación eficiente de imágenes usando FAISS y embeddings.
6. Procesamiento batch de imágenes para mayor velocidad.
7. Manejo robusto de errores y logs para depuración.
8. Todas las rutas se gestionan desde la raíz del proyecto: `/home/jecla2517/Escritorio/programacion/ordenar imagenes`.

El objetivo principal es facilitar la clasificación de colecciones de fanarts, capturas o carátulas asociadas a series listadas en una hoja de cálculo, con ayuda de modelos de IA para mayor precisión y automatización.

---

## Requisitos

* **Python 3.8+** (probado con 3.12). Se recomienda entorno virtual.
* **pandas** (>=2.1,<4), **torch**, **open_clip_torch**, **faiss-cpu**, **ultralytics**, **pillow**, **opencv-python**, **pyside6**.

Opcionales para revisión interactiva (OCR/gestos visuales):
* `Pillow`, `pytesseract`, `imagehash`, `python3-tk` (la GUI usa tkinter).
  Instálalos con `pip install .[ocr]` o manualmente.

> Si prefieres no usar pandas, puedes modificar `read_excel_to_dataframe` para otra librería, pero las demás funciones esperan un **DataFrame** de pandas.

---


## Mejoras recientes

- Modelos de IA (CLIP, YOLO) se cargan solo una vez para eficiencia.
- Detección de personajes mejorada con umbral de confianza y nombres legibles.
- Embeddings y búsquedas optimizadas con FAISS, soporte para batch processing.
- Manejo de errores y logs en todas las funciones de IA.
- Tablas SQL generadas en mayúsculas y ordenadas alfabéticamente.
- Todas las rutas se gestionan desde la raíz del proyecto para evitar errores de ubicación.
- Código más robusto y fácil de depurar.

---


## Comandos principales

El script se puede ejecutar directamente o instalando el paquete (ver más abajo). Todas las rutas deben ser absolutas o relativas a:

`/home/jecla2517/Escritorio/programacion/ordenar imagenes`

Por ejemplo:

- Excel: `/home/jecla2517/Escritorio/programacion/ordenar imagenes/lista.xlsx`
- Imágenes: `/home/jecla2517/Escritorio/programacion/ordenar imagenes/imagenes/`
- Salida: `/home/jecla2517/Escritorio/programacion/ordenar imagenes/filtrada/`
- Imágenes: `~/Escritorio/anime`
- Salida: `~/Escritorio/filtrada`
- Base de datos SQLite: `animes.db` dentro del directorio de salida

```sh
python "anime_organizer.py" \
    --excel "~/Escritorio/lista de animes actualizacion.xlsx" \
    --images "~/Escritorio/anime" \
    --output "~/Escritorio/filtrada" \
    --modo mover --verbose
```

Ejecuta `python anime_organizer.py -h` o `anime-organizer -h` para ver todas las
opciones, entre las que destacan:

* `--modo` : `mover` (predeterminado) o `copiar` imágenes.
* `--review` : revisión interactiva mediante ventanas con OCR.
* `--text-review` : revisión en modo texto/terminal (para servidores o SSH).
* `--columna` : nombre(s) de columna del Excel a usar; por defecto se usan
  todas las columnas de texto.
* `--filter-duplicates` : elimina de "por ver" los títulos que ya aparecen en
  "vistos" cuando ambas columnas existen.
* `--ignore-words` : añade palabras a ignorar durante la normalización, como
  `PORTADA,LATINO` o cualquier otra.
* `--create-shortcut` : crea un acceso directo en el escritorio para lanzar
  rápidamente la aplicación.
* `--verbose` : activa mensajes de depuración en la salida y en el log.

---

## Qué hace internamente

1. **Entrada**: la hoja se lee con `pandas.read_excel`; si la función de lectura
   devuelve algo que no es un `DataFrame` real se convierte o aborta con error
   (esto cubre casos raros como los que provocaron errores de `applymap`).
2. Convierte todos los valores de texto a mayúsculas y ordena las filas.
   (Se utiliza `df.map` para compatibilidad con pandas 3, que eliminó
   `applymap`.)
3. Cada columna se guarda en su propia tabla SQLite (nombre saneado con
   `sanitize_name`).
4. **Nombres válidos** se obtienen uniendo todas las columnas de tipo `object`
   y `string` para ser compatibles con versiones futuras de pandas.
5. Si se solicita, filtra duplicados entre "por ver" y "vistos".
6. Sanea el directorio de salida existente: elimina carpetas no válidas y
   renombra las que sólo difieren en mayúsculas o caracteres.
7. Crea carpetas nuevas para cada nombre válido, usando `sanitize_name` para
   generar nombres seguros.
8. Recorre el directorio de imágenes y mueve/copia cada archivo cuyo nombre
   base (sin extensión) coincide con un nombre válido, renombrándolo a
   `ANIME#N.ext`.
9. Si quedan imágenes sin emparejar y `--review` está activado, inicia el
   flujo de revisión interactiva que muestra cada imagen, el texto OCR detectado
   y sugiere carpetas mediante coincidencias difusas e imágenes similares.

---

## Instalación como paquete

Al instalar con `pip` el proyecto se registra como paquete y añade el script
`anime-organizer`:

```sh
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools
pip install .          # o pip install -e . para desarrollo editable
```

A partir de entonces puedes ejecutar:

```sh
anime-organizer --excel ruta.xlsx --images ruta/imagenes --output salida
```

---

## Interfaz gráfica (GUI)

Si prefieres no usar la línea de comandos existe un wrapper muy sencillo basado
en `tkinter`. Ejecuta `python gui.py` desde el repositorio o usa el comando
`anime-organizer` con el flag `--gui` si lo habilitas.

La ventana proporciona campos para las rutas, modo, palabras a ignorar, y un
botón para ejecutar. El campo "Ejemplo nombre" muestra cómo se normalizará el
texto en tiempo real.

---

## Crear ejecutable

Para distribuir la aplicación en Windows puedes generar un solo `.exe` con
PyInstaller:

```sh
pip install pyinstaller
pyinstaller --onefile "anime_organizer.py" --name anime-organizer.exe
```

El resultado queda en `dist/`. Si lo deseas, añade `--icon=icono.ico` y
`--noconfirm`.

También hay un ejemplo de `run_anime.bat` junto al código para arrancar el
programa en Windows sin parámetros.

---

## Dependencias y versiones

- `pandas>=2.1,<4` (la restricción evita incompatibilidades con pandas 3 o 4).
- Opcionales: `pillow`, `pytesseract`, `imagehash`, `python-dateutil`, etc.

El fichero `requirements.txt` contiene la misma pinning para facilitar la
instalación con `pip install -r requirements.txt`.

---

## Pruebas

Se incluye una suite de `pytest` con 13 pruebas que cubren lectura de Excel,
creación de tablas SQL, normalización de nombres, limpieza de directorios,
revisión interactiva (simulada) y compatibilidad con pandas 3. Inspecciona
`tests/test_anime.py` para detalles.

Ejecuta `pytest -q` para validar todo.

---

## Notas adicionales

- El código aplica saneamientos de nombre para evitar caracteres no válidos en
  nombres de carpeta y limita la longitud a 255 bytes.
- Los registros se escriben en `anime_organizer.log` dentro del directorio de
  salida; activa `--verbose` para más detalle.
- Las funciones y la estructura se eligieron para facilitar futuras mejoras
  (por ejemplo, añadir un motor de búsqueda o soporte para otros formatos).

---

## Problemas comunes con el modelo AI

- La primera vez que uses la app, descargará el modelo open_clip (~600MB) desde Hugging Face. Esto puede tardar varios minutos según tu conexión.
- Para acelerar la descarga, inicia sesión con tu cuenta de Hugging Face ejecutando:
  ```bash
  huggingface-cli login
  ```
  O deja que la app lo solicite automáticamente la primera vez.
- Si tienes problemas de red o la descarga es muy lenta, puedes descargar manualmente el modelo desde [Hugging Face](https://huggingface.co/openai/clip-vit-base-patch32) y colocarlo en `~/.cache/open_clip`.
- Si la app se queda bloqueada descargando el modelo, verifica tu conexión o descarga el modelo manualmente.
- La GUI mostrará el progreso de la descarga del modelo si es necesario.

¡Disfruta organizando tus animes!

- Integración con MyAnimeList: al crear la base de datos, se consulta la API de MAL para cada anime y se agregan automáticamente las columnas de calificación, temporada, episodios y géneros.
- Es necesario un MAL_CLIENT_ID (ver https://myanimelist.net/apiconfig). Si no lo tienes, la app te lo pedirá la primera vez.
