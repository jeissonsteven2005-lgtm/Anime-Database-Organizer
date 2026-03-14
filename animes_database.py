#!/usr/bin/env python3
import pandas as pd
import sqlite3
import os
import sys
import time
from pathlib import Path

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

def main():
    print("Cargando Excel...")
    # Wait for lock
    lock_file = f'.~lock.{EXCEL_FILE}#'
    if os.path.exists(lock_file):
        print("Esperando cierre Excel...")
        while os.path.exists(lock_file):
            time.sleep(1)
    
    df = pd.read_excel(EXCEL_FILE)
    print(df.head())
    print("Columnas:", df.columns.tolist())
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tables
    tables = {
        'ANIMES_VISTOS': 'title TEXT PRIMARY KEY, rating REAL, episodes INTEGER, seasons TEXT, genres TEXT',
        'ANIMES_POR_VER': 'title TEXT PRIMARY KEY, rating REAL, episodes INTEGER, seasons TEXT, genres TEXT',
        'PELICULAS_ANIME': 'title TEXT PRIMARY KEY, rating REAL, episodes INTEGER, seasons TEXT, genres TEXT',
        'MANHUAS_VISTOS': 'title TEXT PRIMARY KEY',
        'MANHUAS_POR_VER': 'title TEXT PRIMARY KEY'
    }
    
    for table, schema in tables.items():
        c.execute(f'DROP TABLE IF EXISTS {table}')
        c.execute(f'CREATE TABLE {table} ({schema})')
    
# MAL Client ID hardcoded
    client_id = "02f49b142f059c7b7379e07aff06356d"
    
    anime_tables = ['ANIMES_VISTOS', 'ANIMES_POR_VER', 'PELICULAS_ANIME']
    
    for table in df.columns:
        if table in tables:
            print(f"\nProcesando {table}...")
            titles = df[table].dropna().astype(str).tolist()
            for title in titles:
                title = title.strip()
                if not title:
                    continue
                
                # Enrich anime tables
                extra = {}
                if table in anime_tables and client_id:
                    extra = get_mal_info(title, client_id)
                
                if table in anime_tables:
                    c.execute(f"""
                        INSERT OR REPLACE INTO {table} VALUES (?, ?, ?, ?, ?)
                    """, (title, extra.get('rating'), extra.get('episodes'), 
                          f"{extra.get('season', '')} {extra.get('year', '')}".strip(), extra.get('genres', '')))
                else:
                    c.execute(f"INSERT OR IGNORE INTO {table} (title) VALUES (?)", (title,))
                
                # Folders from ANIMES_VISTOS
                if table == 'ANIMES_VISTOS':
                    folder_name = title.replace(' ', '_').replace('-', '_').lower()[:50]  # Safe name
                    os.makedirs(folder_name, exist_ok=True)
                    print(f"Creada carpeta: {folder_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\nDB creada: {DB_FILE}")
    print("Carpetas creadas desde ANIMES_VISTOS.")
    print("Verificar: sqlite3 animes.db '.tables' y '.schema'")
    if client_id:
        print("Datos enriquecidos con MAL.")
    else:
        print("MAL saltado (agrega ID en próxima ejecución).")

if __name__ == "__main__":
    main()

