#!/usr/bin/env python3
"""
🎌 Anime Renamer Tool - Herramienta Independiente de Renombrado

Esta herramienta permite renombrar carpetas e imágenes de anime basándose
en la base de datos, de forma independiente al proceso de organización.

Uso:
    python3 rename_tool.py --output "carpeta_filtrada/" [--excel "lista.xlsx"]

Opciones:
    --output    Carpeta donde están las imágenes/carpetas a renombrar
    --excel     Archivo Excel (opcional, por defecto busca en el directorio padre)
    --help      Muestra esta ayuda
"""

import os
import sys
import sqlite3
import argparse
import logging
from pathlib import Path

def sanitize_name(name: str) -> str:
    """
    Reemplaza caracteres no válidos para carpetas y convierte a mayúscula.
    """
    import re
    sanitized = str(name).upper()
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", sanitized)
    return sanitized[:255]

def setup_logging():
    """Configura el logging para la herramienta"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('rename_tool.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def find_excel_file(output_dir: str) -> str:
    """Busca el archivo Excel en el directorio padre de output"""
    parent_dir = Path(output_dir).parent
    possible_names = [
        "lista de animes actualización.xlsx",
        "lista.xlsx",
        "animes.xlsx"
    ]

    for name in possible_names:
        excel_path = parent_dir / name
        if excel_path.exists():
            return str(excel_path)

    return None

def update_database_from_excel(excel_path: str) -> bool:
    """Actualiza la base de datos desde Excel si es necesario"""
    try:
        script_dir = Path(__file__).parent.parent
        db_script = script_dir / "db_create.sh"

        if db_script.exists():
            import subprocess
            result = subprocess.run(["bash", str(db_script)],
                                  cwd=script_dir,
                                  capture_output=True,
                                  text=True)
            if result.returncode == 0:
                logging.info("Base de datos actualizada correctamente")
                return True
            else:
                logging.error(f"Error actualizando BD: {result.stderr}")
                return False
        else:
            logging.warning("Script de base de datos no encontrado")
            return False
    except Exception as e:
        logging.error(f"Error en actualización de BD: {e}")
        return False

def get_correct_names_from_db(db_path: str) -> set:
    """Obtiene los nombres correctos solo de ANIMES_VISTOS"""
    correct_names = set()

    if not os.path.exists(db_path):
        logging.error(f"Base de datos no encontrada: {db_path}")
        return correct_names

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Solo leer de ANIMES_VISTOS
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ANIMES_VISTOS'")
        tables = cursor.fetchall()

        for table_name, in tables:
            try:
                cursor.execute(f'SELECT title FROM "{table_name}"')
                titles = cursor.fetchall()
                for title, in titles:
                    if title and title.strip():
                        correct_names.add(title.strip().upper())
            except sqlite3.Error as e:
                logging.warning(f"Error leyendo tabla {table_name}: {e}")

        conn.close()
        logging.info(f"Encontrados {len(correct_names)} títulos en ANIMES_VISTOS")

    except sqlite3.Error as e:
        logging.error(f"Error conectando a BD: {e}")

    return correct_names

def rename_folders_and_images(output_dir: str, correct_names: set) -> tuple[int, int]:
    """
    Renombra carpetas e imágenes basándose en los nombres correctos

    Returns:
        tuple: (carpetas_renombradas, imagenes_renombradas)
    """
    if not os.path.exists(output_dir):
        logging.error(f"Directorio de salida no existe: {output_dir}")
        return 0, 0

    renamed_folders = 0
    renamed_images = 0

    # Crear mapa de renombrado de carpetas
    folder_mapping = {}

    for existing_folder in os.listdir(output_dir):
        existing_path = os.path.join(output_dir, existing_folder)
        if not os.path.isdir(existing_path):
            continue

        # Buscar el nombre correcto más similar
        existing_upper = existing_folder.upper()
        best_match = None
        best_score = 0

        for correct_name in correct_names:
            # Calcular similitud simple
            if correct_name in existing_upper or existing_upper in correct_name:
                score = len(set(correct_name.split()) & set(existing_upper.split()))
                if score > best_score:
                    best_score = score
                    best_match = correct_name

        if best_match and best_match != existing_upper:
            folder_mapping[existing_folder] = best_match
        elif best_match:
            folder_mapping[existing_folder] = best_match
        else:
            # Si no hay match, usar el nombre existente en mayúscula
            folder_mapping[existing_folder] = existing_upper

    # Renombrar carpetas
    for old_name, new_name in folder_mapping.items():
        if old_name != new_name:
            old_path = os.path.join(output_dir, old_name)
            new_path = os.path.join(output_dir, new_name)

            try:
                os.rename(old_path, new_path)
                logging.info(f"📁 Renombrada carpeta: {old_name} → {new_name}")
                renamed_folders += 1
            except OSError as e:
                logging.error(f"⚠️ Error renombrando carpeta {old_name}: {e}")
                continue

            # Usar la nueva ruta para renombrar imágenes
            folder_path = new_path
            folder_name = new_name
        else:
            folder_path = os.path.join(output_dir, old_name)
            folder_name = old_name

        # Renombrar imágenes dentro de la carpeta
        if os.path.exists(folder_path):
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']
            images = [f for f in os.listdir(folder_path)
                     if any(f.lower().endswith(ext) for ext in image_extensions)]
            images.sort()  # Ordenar para consistencia

            for i, img_name in enumerate(images, 1):
                img_path = os.path.join(folder_path, img_name)
                _, ext = os.path.splitext(img_name)

                new_img_name = f"{folder_name} # {i}{ext}"
                new_img_path = os.path.join(folder_path, new_img_name)

                try:
                    os.rename(img_path, new_img_path)
                    logging.info(f"🖼️ Renombrada imagen: {img_name} → {new_img_name}")
                    renamed_images += 1
                except OSError as e:
                    logging.error(f"⚠️ Error renombrando imagen {img_name}: {e}")

    return renamed_folders, renamed_images

def main():
    parser = argparse.ArgumentParser(
        description="🎌 Anime Renamer Tool - Renombrado independiente de carpetas e imágenes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Carpeta donde están las imágenes/carpetas a renombrar"
    )

    parser.add_argument(
        "--excel", "-e",
        help="Archivo Excel (opcional, por defecto busca automáticamente)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Salida detallada"
    )

    args = parser.parse_args()

    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    setup_logging()

    logging.info("🎌 Iniciando Anime Renamer Tool")
    logging.info(f"Directorio de salida: {args.output}")

    # Resolver rutas absolutas
    output_dir = os.path.abspath(args.output)

    # Encontrar archivo Excel
    excel_path = args.excel
    if not excel_path:
        excel_path = find_excel_file(output_dir)
        if excel_path:
            logging.info(f"Excel encontrado automáticamente: {excel_path}")
        else:
            logging.error("No se pudo encontrar archivo Excel")
            return 1

    if not os.path.exists(excel_path):
        logging.error(f"Archivo Excel no encontrado: {excel_path}")
        return 1

    # Actualizar base de datos
    logging.info("Actualizando base de datos...")
    if not update_database_from_excel(excel_path):
        logging.warning("No se pudo actualizar la BD, intentando usar existente")

    # Obtener nombres correctos
    db_path = os.path.join(os.path.dirname(excel_path), "animes.db")
    correct_names = get_correct_names_from_db(db_path)

    if not correct_names:
        logging.error("No se encontraron nombres correctos en la base de datos")
        return 1

    # Ejecutar renombrado
    logging.info("Iniciando proceso de renombrado...")
    try:
        renamed_folders, renamed_images = rename_folders_and_images(output_dir, correct_names)

        logging.info("✅ ¡RENOMBRADO COMPLETADO!")
        logging.info(f"📁 Carpetas renombradas: {renamed_folders}")
        logging.info(f"🖼️ Imágenes renombradas: {renamed_images}")

        print("\n🎉 Renombrado completado exitosamente!")
        print(f"📁 Carpetas renombradas: {renamed_folders}")
        print(f"🖼️ Imágenes renombradas: {renamed_images}")

        return 0

    except Exception as e:
        logging.error(f"Error durante el renombrado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())