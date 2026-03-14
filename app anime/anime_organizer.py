if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en anime_organizer.py:\n{e}\n\n{traceback.format_exc()}")
import os
from mal_api import get_mal_info
# Enriquecer DataFrame con datos de MyAnimeList
def enrich_with_mal(df, client_id):
    import time
    if 'rating' not in df.columns:
        df['rating'] = None
    if 'episodes' not in df.columns:
        df['episodes'] = None
    if 'season' not in df.columns:
        df['season'] = None
    if 'year' not in df.columns:
        df['year'] = None
    if 'genres' not in df.columns:
        df['genres'] = None
    for idx, row in df.iterrows():
        title = row[df.columns[0]] if len(df.columns) > 0 else None
        if title and (pd.isna(row.get('rating')) or row.get('rating') is None):
            info = get_mal_info(str(title), client_id)
            if info:
                df.at[idx, 'rating'] = info.get('rating')
                df.at[idx, 'episodes'] = info.get('episodes')
                df.at[idx, 'season'] = info.get('season')
                df.at[idx, 'year'] = info.get('year')
                df.at[idx, 'genres'] = info.get('genres')
            time.sleep(0.5)  # evitar rate limit
    return df
#!/usr/bin/env python3
"""Utilidad sencilla para leer un archivo Excel con nombres de animes, guardar
los datos en una base de datos SQLite y organizar una colección de imágenes en
una estructura de carpetas basada en los nombres de los animes.

Uso:
    python anime_organizer.py \
        --excel animes.xlsx \
        --images imagenes \
        --output Organizados \
        --database animes.db

El script creará el directorio de salida si no existe, generará una
subcarpeta por cada valor único de la columna "Nombre" del libro de
cálculo y copiará cualquier imagen cuyo nombre de archivo (sin extensión)
coincida con uno de los nombres de anime en la carpeta correspondiente.
Las imágenes que no coincidan se listan pero se dejan donde están.

Requisitos
----------
* Python 3.8+
* pandas

Además de crear carpetas para los nombres listados, el directorio de salida se
revisa en cada ejecución: las subcarpetas que ya no corresponden a ningún anime
válido se borran, y las que tienen el nombre correcto pero en formato distinto
(sean sólo minúsculas, espacios extra, etc.) se renombrarán automáticamente.

"""

import argparse
import logging
import os
import re
import shutil
import sqlite3
import sys

try:
    import pandas as pd
except ImportError:
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    logging.error("El paquete 'pandas' no está instalado. Instálalo e inténtalo de nuevo.")
    sys.exit(1)


def read_excel_to_dataframe(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Archivo Excel no encontrado: {path}")
    try:
        return pd.read_excel(path)
    except Exception as e:  # pandas will raise for corrupt files
        raise RuntimeError(f"Error leyendo el Excel: {e}")


def dataframe_to_sql(df: pd.DataFrame, db_path: str, table: str = "animes"):
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table, conn, if_exists="replace", index=False)
    finally:
        conn.close()


def sanitize_name(name: str) -> str:
    # reemplaza caracteres no válidos para nombres de carpeta por guión bajo
    # evita longitud excesiva
    sanitized = re.sub(r"[\\/:*?\"<>|]", "_", name)
    return sanitized[:255]


def make_directories(base: str, names):
    os.makedirs(base, exist_ok=True)
    for name in names:
        safe = sanitize_name(str(name).upper())
        folder = os.path.join(base, safe)
        os.makedirs(folder, exist_ok=True)


def fix_directory_names(base: str, valid_names):
    """Renombra carpetas existentes para que coincidan con la versión saneada de
    los nombres válidos.

    Si el usuario crea manualmente un directorio con el nombre correcto pero
    con mayúsculas/minúsculas o caracteres distintos, esta función lo reubica.
    """
    valid_map = {sanitize_name(v).upper(): sanitize_name(v) for v in valid_names}
    if not os.path.isdir(base):
        return
    for entry in os.listdir(base):
        path = os.path.join(base, entry)
        if not os.path.isdir(path):
            continue
        key = entry.upper()
        if key in valid_map:
            desired = valid_map[key]
            if entry != desired:
                newpath = os.path.join(base, desired)
                # si ya existe el destino, intenta eliminar el original
                if os.path.exists(newpath):
                    shutil.rmtree(path)
                else:
                    os.rename(path, newpath)
                logging.info("Carpeta renombrada: %s -> %s", entry, desired)


def cleanup_directories(base: str, valid_names):
    """Elimina carpetas que no correspondan a ningún anime válido."""
    valid_set = {sanitize_name(v).upper() for v in valid_names}
    if not os.path.isdir(base):
        return
    for entry in os.listdir(base):
        path = os.path.join(base, entry)
        if not os.path.isdir(path):
            continue
        if entry.upper() not in valid_set:
            try:
                shutil.rmtree(path)
                logging.info("Carpeta eliminada (no válida): %s", entry)
            except Exception as e:
                logging.warning("No pude borrar %s: %s", entry, e)


def _learning_path(base_dir: str) -> str:
    return os.path.join(base_dir, "learning.json")


def load_learning(base_dir: str) -> dict:
    """Carga el diccionario de aprendizaje desde el directorio de salida.

    El formato es JSON con clave=norm (o similar) y valor=carpeta elegida.
    """
    path = _learning_path(base_dir)
    if os.path.isfile(path):
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logging.warning("No pude cargar el aprendizaje desde %s", path)
    return {}


def save_learning(base_dir: str, mapping: dict):
    path = _learning_path(base_dir)
    try:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning("Error guardando aprendizaje: %s", e)


def suggest_names(norm, valid_names, learning=None):
    """Devuelve una lista de nombres sugeridos a partir de *norm*.

    La lista incluye:
    * coincidencias exactas/por contención
    * resultados difusos (`difflib`) para variantes similares
    * primero cualquier carpeta aprendida previamente a partir del nombre
      normalizado
    """
    from difflib import get_close_matches
    suggestions = []
    # primero usar aprendizaje previo si existe
    if learning and norm:
        # buscar coincidencias cercanas en las claves aprendidas
        for key, val in learning.items():
            if norm == key or key in norm or norm in key:
                suggestions.append(val)
        # fuzzy en aprendizaje
        closers = get_close_matches(norm, list(learning.keys()), n=3, cutoff=0.6)
        for k in closers:
            v = learning.get(k)
            if v and v not in suggestions:
                suggestions.append(v)
    for candidate in valid_names:
        if norm and (norm == candidate or norm in candidate or candidate in norm):
            if candidate not in suggestions:
                suggestions.append(candidate)
    # fuzzy matching en valid_names
    closers = get_close_matches(norm, list(valid_names), n=5, cutoff=0.6)
    for c in closers:
        if c not in suggestions:
            suggestions.append(c)
    return suggestions


def review_images(images_dir: str, unmatched, valid_names, base_dir: str, move: bool = False, chooser=None):
    """Recorre las imágenes no emparejadas y permite al usuario decidir.

    Se intenta extraer texto de cada imagen con OCR (`pytesseract`) y buscar
    coincidencias en `valid_names`. El usuario ve la imagen y puede moverla al
    directorio sugerido, elegir otra carpeta o ignorarla.

    Si se pasa el parámetro *chooser* (una función), será usada para obtener la
    elección en lugar de abrir una ventana gráfica. Esto facilita las pruebas
    y permite ejecutar revisiones en modo texto.

    Requiere Pillow y pytesseract; si no están disponibles se registra una
    advertencia y no hace nada.
    """
    import tkinter as tk
    try:
        from PIL import Image, ImageTk
    except ImportError:
        logging.warning("Pillow no instalado; no es posible la revisión interactiva.")
        return
    try:
        import pytesseract
    except ImportError:
        logging.warning("pytesseract no instalado; no es posible la revisión interactiva.")
        pytesseract = None
    try:
        import imagehash
    except ImportError:
        imagehash = None

    # opcional: precomputar hashes de imágenes ya ordenadas para sugerir carpetas
    hash_map = {}
    if imagehash and os.path.isdir(base_dir):
        for folder in os.listdir(base_dir):
            folderpath = os.path.join(base_dir, folder)
            if not os.path.isdir(folderpath):
                continue
            hashes = []
            for f in os.listdir(folderpath):
                fp = os.path.join(folderpath, f)
                try:
                    img = Image.open(fp)
                    hashes.append(imagehash.average_hash(img))
                except Exception:
                    pass
            if hashes:
                hash_map[folder] = hashes

    # load any existing learning data for this output folder
    learning = load_learning(base_dir)

    root = tk.Tk()
    root.withdraw()  # no mostrar ventana principal

    def ask_for_file(fname, ocr_text, suggestions):
        dialog = tk.Toplevel()
        dialog.transient(root)
        dialog.focus_set()
        dialog.title(f"Revisar: {fname}")
        # mostrar imagen redimensionada si es demasiado grande
        try:
            img = Image.open(os.path.join(images_dir, fname))
        except Exception:
            img = None
        if img:
            maxw, maxh = 500, 400
            w, h = img.size
            if w > maxw or h > maxh:
                img = img.resize((min(w, maxw), min(h, maxh)))
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(dialog, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=0, columnspan=3)
        tk.Label(dialog, text=f"OCR: {ocr_text}").grid(row=1, column=0, columnspan=3, sticky="w")
        # botones para sugerencias
        if suggestions:
            tk.Label(dialog, text="Sugerencias:").grid(row=2, column=0, sticky="w")
            # ubicar botones en filas sucesivas para evitar solapamiento
            start_row = 3
            for idx, sug in enumerate(suggestions):
                def make_handler(s=sug):
                    def handler():
                        dialog.choice = s
                        dialog.destroy()
                    return handler
                btn = tk.Button(dialog, text=sug, command=make_handler())
                btn.grid(row=start_row + idx, column=0, sticky="w", padx=2)
            next_input_row = start_row + len(suggestions)
        input_row = next_input_row if 'next_input_row' in locals() else 3
        tk.Label(dialog, text="Otra carpeta:").grid(row=input_row, column=0, sticky="e")
        entry_var = tk.StringVar()
        tk.Entry(dialog, textvariable=entry_var, width=40).grid(row=input_row, column=1)
        def move_it():
            dialog.choice = entry_var.get().strip()
            dialog.destroy()
        def skip_it():
            dialog.choice = None
            dialog.destroy()
        btn_row = input_row + 1
        tk.Button(dialog, text="Mover/Asignar", command=move_it).grid(row=btn_row, column=0)
        tk.Button(dialog, text="Omitir", command=skip_it).grid(row=btn_row, column=1)
        dialog.grab_set()
        root.wait_window(dialog)
        return dialog.choice

    if chooser is None:
        chooser = ask_for_file

    for fname in unmatched:
        ocr_text = ""
        if pytesseract:
            try:
                img = Image.open(os.path.join(images_dir, fname))
                ocr_text = pytesseract.image_to_string(img)
            except Exception:
                ocr_text = ""
        norm = normalise_image_name(ocr_text or fname)
        suggestions = suggest_names(norm, valid_names, learning=learning)
        # si no hay sugerencia de texto, mirar similitud con imágenes ya clasificadas
        if not suggestions and imagehash and hash_map:
            try:
                h = imagehash.average_hash(Image.open(os.path.join(images_dir, fname)))
                for folder, hashes in hash_map.items():
                    for hh in hashes:
                        if h - hh < 5:
                            if folder not in suggestions:
                                suggestions.append(folder)
                            break
            except Exception:
                pass
        choice = chooser(fname, ocr_text, suggestions)
        logging.info("Revisión: %s -> %s", fname, choice or "omitido")
        if choice:
            # save learning mapping
            if norm:
                learning[norm] = choice
                save_learning(base_dir, learning)
            safe_folder = sanitize_name(choice)
            dest_folder = os.path.join(base_dir, safe_folder)
            os.makedirs(dest_folder, exist_ok=True)
            src = os.path.join(images_dir, fname)
            dst = os.path.join(dest_folder, fname)
            if move:
                shutil.move(src, dst)
            else:
                shutil.copy(src, dst)
        # si choice es None se omite
    root.destroy()


def normalise_image_name(name: str, ignore_words=None) -> str:
    """Convierte un nombre de archivo en una forma comparable.

    - Reemplaza guiones bajos por espacios
    - Elimina las palabras de `ignore_words` (e.g. PORTADA, LATINO, SUB, ...)
    - Elimina dígitos finales
    - Devuelve en mayúsculas
    """
    if ignore_words is None:
        # palabras ignoradas por defecto; añadir aquí más según necesidades
        ignore_words = ["PORTADA", "LATINO", "DESUPORTADA"]
    s = name.replace("_", " ")
    s = s.upper()
    # suprimir palabras extra incluso dentro de otras palabras; procesar más largas primero
    for w in sorted(ignore_words, key=len, reverse=True):
        s = s.replace(w.upper(), "")
    # quitar números al final
    s = re.sub(r"\d+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def organise_images(images_dir: str, base_dir: str, valid_names, move: bool = False, ignore_words=None):
    if not os.path.isdir(images_dir):
        raise FileNotFoundError(f"Directorio de imágenes no encontrado: {images_dir}")

    unmatched = []
    counters = {}  # nombre -> número consecutivo
    # ensure valid_names are uppercase strings
    valid_names = {str(n).upper() for n in valid_names}

    for fname in os.listdir(images_dir):
        if fname.startswith("."):
            continue
        full = os.path.join(images_dir, fname)
        if not os.path.isfile(full):
            continue

        name, ext = os.path.splitext(fname)
        norm = normalise_image_name(name, ignore_words=ignore_words)
        match = None
        # buscar coincidencia por igualdad o contención
        for candidate in valid_names:
            if norm == candidate or norm.startswith(candidate) or candidate in norm:
                match = candidate
                break

        if match:
            safe_folder = sanitize_name(match)
            dest_folder = os.path.join(base_dir, safe_folder)
            idx = counters.get(match, 0) + 1
            counters[match] = idx
            new_fname = f"{safe_folder}#{idx}{ext}"
            dest_path = os.path.join(dest_folder, new_fname)
            if move:
                shutil.move(full, dest_path)
            else:
                shutil.copy(full, dest_path)
        else:
            unmatched.append(fname)

    total = sum(counters.values())
    logging.info("Procesadas %d imágenes." , total)
    if unmatched:
        logging.warning("Las siguientes imágenes no coincidieron con ningún nombre de anime:")
        for u in unmatched:
            logging.warning("  %s", u)
    return unmatched


def create_desktop_shortcut():
    """Crea un acceso directo en el escritorio al ejecutable o script."""
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")
    if not os.path.isdir(desktop):
        logging.warning("No se encontró el escritorio en %s", desktop)
        return
    # determinar comando de lanzamiento
    script = os.path.abspath(sys.argv[0])
    if script.endswith(".py"):
        cmd = f"{sys.executable} \"{script}\""
    else:
        cmd = script
    if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
        fname = os.path.join(desktop, "anime-organizer.desktop")
        content = f"""[Desktop Entry]
Type=Application
Name=Anime Organizer
Exec={cmd}
Terminal=true
"""
        try:
            with open(fname, "w") as f:
                f.write(content)
            os.chmod(fname, 0o755)
            logging.info("Acceso directo creado en %s", fname)
        except Exception as e:
            logging.error("Error creando accesos directo: %s", e)
    elif sys.platform.startswith("win"):
        # no se implementa creación de .lnk automática
        logging.info("En Windows, crea un acceso directo manualmente al .exe o al script")
    else:
        logging.warning("Sistema operativo no soportado para atajo de escritorio")


def main():
    parser = argparse.ArgumentParser(
        description="Organizar imágenes de anime según un archivo Excel de nombres."
    )
    parser.add_argument("--excel", required=False, help="Ruta al archivo Excel (por defecto en el Escritorio: 'lista de animes actualizacion.xlsx')")
    parser.add_argument("--images", required=False, help="Directorio con las imágenes (por defecto en el Escritorio: 'anime')")
    parser.add_argument(
        "--output", default=os.path.expanduser("~/Escritorio/filtrada"),
        help="Directorio base para la salida organizada (por defecto '$HOME/Escritorio/filtrada')"
    )
    parser.add_argument(
        "--database", default=None, help="Archivo de base de datos SQLite a crear (por defecto dentro del directorio de salida)")
    parser.add_argument(
        "--columna", default=None,
        help="Nombre de la columna en el Excel que contiene los títulos (si se omite se usan todas las columnas)"
    )
    parser.add_argument(
        "--modo", choices=["copiar", "mover"], default="mover",
        help="Qué hacer con las imágenes: mover (predeterminado) o copiar"
    )
    parser.add_argument(
        "--filter-duplicates", action="store_true",
        help="Si existen las dos columnas ANIMES POR VER y ANIMES VISTOS, eliminar del primero los que aparecen en el segundo"
    )
    parser.add_argument(
        "--ignore-words", default="", help="Lista de palabras adicionales a ignorar al normalizar nombres, separadas por comas"
    )
    parser.add_argument(
        "--create-shortcut", action="store_true",
        help="Crear un acceso directo en el escritorio para lanzar la aplicación"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Mostrar mensajes de depuración"
    )
    parser.add_argument(
        "--review", action="store_true",
        help="Iniciar revisión interactiva de imágenes que no coincidieron (requiere PIL/pytesseract)"
    )
    parser.add_argument(
        "--text-review", action="store_true",
        help="Usar revisión interactiva en modo texto/terminal en lugar de ventanas GUI"
    )
    args = parser.parse_args()

    if args.create_shortcut:
        create_desktop_shortcut()

    # configuración de logging: consola + fichero en la carpeta de salida
    level = logging.DEBUG if args.verbose else logging.INFO
    log_file = os.path.join(args.output, "anime_organizer.log")
    handlers = [logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")]
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level, handlers=handlers)
    logging.debug("Registro en %s", log_file)

    # auto‑valores si no se dan
    if not args.excel:
        args.excel = os.path.expanduser("~/Escritorio/lista de animes actualizacion.xlsx")
        logging.debug("Usando Excel por defecto: %s", args.excel)
    args.excel = os.path.expanduser(args.excel)

    if not args.images:
        args.images = os.path.expanduser("~/Escritorio/anime")
        logging.debug("Usando directorio de imágenes por defecto: %s", args.images)
    args.images = os.path.expanduser(args.images)

    if args.database is None:
        args.database = os.path.join(args.output, "animes.db")
        logging.debug("Base de datos por defecto: %s", args.database)
    args.database = os.path.expanduser(args.database)

    args.output = os.path.expanduser(args.output)
    os.makedirs(args.output, exist_ok=True)
    do_review = args.review
    text_review = args.text_review

    # Enriquecer con datos de MyAnimeList
    # MAL omitido (mal_api no disponible)
    logging.debug("Enriquecimiento MAL omitido.")

    try:
        df = read_excel_to_dataframe(args.excel)
    except Exception as err:
        logging.error(err)
        sys.exit(1)

    # asegurarse de que tenemos un DataFrame real (algunas versiones/engines
    # podrían devolver un objeto similar). Convertimos para evitar errores de
    # atributo como el reportado en la GUI ('DataFrame' object has no
    # attribute 'applymap').
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            logging.error("El objeto leído no es un DataFrame: %r", type(df))
            sys.exit(1)

    # convertir todo a mayúsculas y ordenar filas por todas las columnas
    # pandas 3 eliminó ``DataFrame.applymap``; ``map`` es el reemplazo
    try:
        # Fix compatible con pandas 2.1+ (applymap eliminado)
        df = df.map(lambda x: x.upper() if isinstance(x, str) else x)
    except AttributeError as err:
        logging.error("Error transformando DataFrame: %s", err)
        logging.error("objeto df: %r", type(df))
        sys.exit(1)
    if not df.columns.empty:
        df = df.sort_values(by=list(df.columns))

    # guardar cada columna en su propia tabla
    try:
        conn = sqlite3.connect(args.database)
        for col in df.columns:
            series = df[col].dropna().astype(str).str.strip()
            if series.empty:
                continue
            tbl = sanitize_name(col)
            dfcol = pd.DataFrame({col: series.unique()}).sort_values(by=col)
            dfcol.to_sql(tbl, conn, if_exists="replace", index=False)
    except Exception as err:
        logging.error("Error escribiendo la base de datos: %s", err)
        sys.exit(1)
    finally:
        conn.close()

    # determinar conjuntos de nombres válidos para organizar imágenes
    if args.columna:
        cols = [c.strip().upper() for c in args.columna.split(",")]
        valid_names = set()
        for c in cols:
            if c in df.columns:
                valid_names |= set(df[c].dropna().astype(str))
            else:
                logging.warning("Columna '%s' no encontrada, la ignoro.", c)
    else:
        # unión de todas las columnas de texto.
        # pandas 4 cambiará el comportamiento de ``include='object'``; para
        # ser compatibles con versiones antiguas y nuevas, incluimos también
        # el tipo de cadena explícito.
        valid_names = set(
            df.select_dtypes(include=["object", "string"]).stack().astype(str).unique()
        )

    # filtrado opcional entre listas "por ver" y "vistos"
    if args.filter_duplicates and "ANIMES POR VER" in df.columns and "ANIMES VISTOS" in df.columns:
        por_ver = df["ANIMES POR VER"].dropna().astype(str)
        vistos = df["ANIMES VISTOS"].dropna().astype(str)
        filtrados = por_ver[~por_ver.isin(vistos)]
        valid_names |= set(filtrados)
        # actualizar tabla por_ver con la versión filtrada
        try:
            conn = sqlite3.connect(args.database)
            pd.DataFrame({"ANIME": filtrados.sort_values()}).to_sql(
                "animes_por_ver_filtrados", conn, if_exists="replace", index=False
            )
        finally:
            conn.close()

    # renombrar o eliminar carpetas existentes según la lista actual
    fix_directory_names(args.output, valid_names)
    cleanup_directories(args.output, valid_names)
    # crear directorios de salida basados en nombres válidos (restantes)
    make_directories(args.output, valid_names)
    # construir lista de palabras a ignorar para normalización
    ignore_list = ["PORTADA", "LATINO"]
    if args.ignore_words:
        extra = [w.strip().upper() for w in args.ignore_words.split(",") if w.strip()]
        ignore_list.extend(extra)
    unmatched = organise_images(
        args.images,
        args.output,
        valid_names,
        move=(args.modo == "mover"),
        ignore_words=ignore_list,
    )

    if do_review and unmatched:
        chooser = None
        if text_review:
            def text_chooser(fname, ocr_text, suggestions):
                # mostrar información en terminal y pedir entrada
                print(f"Revisando {fname}")
                if ocr_text:
                    print(f"  OCR: {ocr_text}")
                if suggestions:
                    print("  Sugerencias:")
                    for i, s in enumerate(suggestions, 1):
                        print(f"   {i}. {s}")
                    resp = input("Elige número (o deja vacío para omitir): ")
                    try:
                        idx = int(resp) - 1
                        if 0 <= idx < len(suggestions):
                            return suggestions[idx]
                    except Exception:
                        pass
                return input("Carpeta definitiva (vacío para omitir): ").strip() or None
            chooser = text_chooser
        review_images(
            args.images,
            unmatched,
            valid_names,
            args.output,
            move=(args.modo == "mover"),
            chooser=chooser,
        )

    logging.info("Listo. Salida guardada en %s", args.output)


if __name__ == "__main__":
    main()
