#!/usr/bin/env python3
import pandas as pd
import sqlite3
import os
import sys
import time
import re
from pathlib import Path
import platform

# Add app anime to path for mal_api
sys.path.append('app anime')
try:
    from mal_api import get_mal_info
    MAL_AVAILABLE = True
except ImportError:
    MAL_AVAILABLE = False
    def get_mal_info(title, client_id):
        return {}

EXCEL_FILE = 'lista de animes actualización.xlsx'
DB_FILE = 'animes.db'

def sanitize_name(name: str) -> str:
    # Space to _, invalid chars _, multiple _ one, trim _
    sanitized = re.sub(r'[\\/:*?\"<>| ]', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized[:255]

def main():
    print("Cargando Excel...")
    # Wait lock
    lock_file = f'.~lock.{EXCEL_FILE}#'
    if os.path.exists(lock_file):
        print("Esperando cierre Excel...")
        while os.path.exists(lock_file):
            time.sleep(1)
    
    # Leer Excel sin headers, primera fila es títulos de columnas/tablas
    df = pd.read_excel(EXCEL_FILE, header=None)
    print("Filas x Columnas:", df.shape)
    print(df.head())
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    all_names = set()
    
    # Una tabla por columna, nombre de tabla = primera fila en mayúsculas
    for col_idx in range(df.shape[1]):
        # Primera fila de la columna es el título de la tabla
        table_title = str(df.iloc[0, col_idx]).strip().upper()
        if not table_title:
            continue  # Saltar columnas vacías
        tbl = sanitize_name(table_title)
        print(f"Tabla: {tbl} (columna {col_idx})")
        c.execute(f'DROP TABLE IF EXISTS "{tbl}"')
        c.execute(f'CREATE TABLE "{tbl}" (title TEXT PRIMARY KEY)')
        
        # Valores desde la segunda fila (índice 1) en adelante, en mayúsculas, únicos
        titles = df.iloc[1:, col_idx].dropna().astype(str).str.strip().str.upper().tolist()
        unique_titles = list(set(titles))
        
        for title in unique_titles:
            if not title:
                continue
            all_names.add(title)
            c.execute(f'INSERT OR IGNORE INTO "{tbl}" (title) VALUES (?)', (title,))
    
    # === Completar datos con MAL ===
    if MAL_AVAILABLE:
        client_id = "02f49b142f059c7b7379e07aff06356d"  # Cambia por tu client_id real
        for col_idx in range(df.shape[1]):
            table_title = str(df.iloc[0, col_idx]).strip().upper()
            if not table_title:
                continue
            tbl = sanitize_name(table_title)
            print(f"Consultando MAL para tabla: {tbl}")
            # Obtener todos los títulos de la tabla
            c.execute(f'SELECT title FROM "{tbl}"')
            rows = c.fetchall()
            # Añadir columnas si no existen
            for col in ["rating", "episodes", "season", "year", "genres"]:
                try:
                    c.execute(f'ALTER TABLE "{tbl}" ADD COLUMN {col} TEXT')
                except sqlite3.OperationalError:
                    pass  # Ya existe
            for (title,) in rows:
                info = get_mal_info(title, client_id)
                if info:
                    c.execute(f'UPDATE "{tbl}" SET rating=?, episodes=?, season=?, year=?, genres=? WHERE title=?',
                        (info.get("rating"), info.get("episodes"), info.get("season"), info.get("year"), info.get("genres"), title))
            conn.commit()
        print("Datos de MAL completados en la base de datos.")
    else:
        print("API de MAL no disponible. Solo se crearon los títulos.")
    
    conn.commit()
    conn.close()
    
    print(f"\nDB: {DB_FILE} OK.")
    print("Carpetas creadas para todos los títulos únicos.")
    print(f"sqlite3 {DB_FILE} '.tables'")

    # Crear carpetas SOLO para los títulos de la tabla ANIMES_VISTOS en /filtrar
    FILTRAR_DIR = get_filtrar_dir()
    os.makedirs(FILTRAR_DIR, exist_ok=True)
    try:
        conn2 = sqlite3.connect(DB_FILE)
        c2 = conn2.cursor()
        c2.execute('SELECT title FROM ANIMES_VISTOS')
        rows = c2.fetchall()
        print(f"Creando carpetas en {FILTRAR_DIR} para {len(rows)} animes vistos desde la BD...")
        for (name,) in rows:
            if not name:
                continue
            folder_name = sanitize_name(name)
            # Windows: limita longitud total de ruta a 240 caracteres
            if platform.system() == "Windows":
                full_path = os.path.join(FILTRAR_DIR, folder_name)[:240]
            else:
                full_path = os.path.join(FILTRAR_DIR, folder_name)
            os.makedirs(full_path, exist_ok=True)
            print(f"Creada: {full_path}")
        conn2.close()
    except Exception as e:
        print(f"Error creando carpetas desde la BD: {e}")

if __name__ == "__main__":
    main()

