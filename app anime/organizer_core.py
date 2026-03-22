import re
import os
import shutil
import subprocess
import pandas as pd
import sqlite3
import json
import logging
from typing import Dict, List, Tuple, Optional
from ai_models import predict_anime, get_embedding
from vector_index import ImageIndex
import sys
sys.path.insert(0, os.path.dirname(__file__))
from filter_utils import normalise_image_name, generate_options_sequential, split_words

try:
    from config import IMAGE_EXT
except ImportError:
    IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']

def sanitize_name(name: str) -> str:
    """
    Reemplaza caracteres no válidos para carpetas y convierte a mayúscula.
    """
    sanitized = str(name).upper()
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", sanitized)
    return sanitized[:255]

def match_name_parts_confidence(img_base: str, all_names: set, min_conf=0.7) -> Optional[Tuple[str, float]]:
    """
    Matching jerárquico con confianza mejorado.
    Retorna (folder, confidence) si > min_conf.
    Ahora usa normalización consistente y es menos restrictivo.
    """
    # Normalizar el nombre de la imagen
    norm_img = normalise_image_name(img_base)
    words = norm_img.replace('_', ' ').split()
    
    if not words:
        return None
    
    candidates = set(all_names)
    word_matches = 0
    total_words = len(words)
    
    # Matching más flexible: al menos 50% de palabras deben coincidir
    for word in words:
        word_upper = word.strip().upper()
        if not word_upper or len(word_upper) < 2:  # Ignorar palabras muy cortas
            total_words -= 1
            continue
            
        new_candidates = set()
        for folder in candidates:
            folder_upper = folder.upper()
            # Coincidencia parcial: la palabra está contenida en el nombre del folder
            if word_upper in folder_upper:
                new_candidates.add(folder)
                word_matches += 1
                break  # Al menos una coincidencia por palabra es suficiente
        
        # Si no hay candidatos después de esta palabra, reducir requisitos
        if not new_candidates:
            # Intentar con coincidencia más laxa (al menos 3 caracteres)
            for folder in candidates:
                folder_upper = folder.upper()
                if any(word_upper[i:i+3] in folder_upper for i in range(max(1, len(word_upper)-2))):
                    new_candidates.add(folder)
                    word_matches += 0.5  # Coincidencia parcial cuenta medio
                    break
        
        candidates = new_candidates if new_candidates else candidates
    
    if not candidates or total_words == 0:
        return None
    
    # Calcular confianza basada en porcentaje de palabras coincidentes
    confidence = min(1.0, word_matches / total_words)
    
    # Bonus por longitud de coincidencia
    best_match = max(candidates, key=lambda x: len(x)) if candidates else None
    if best_match and confidence >= min_conf:
        # Bonus si el nombre normalizado es muy similar
        best_norm = normalise_image_name(best_match)
        if norm_img == best_norm:
            confidence = min(1.0, confidence + 0.2)
        return best_match, confidence
    
    return None


def get_similarity_confidence(embedding_neighbors: list, meta: list) -> Optional[Tuple[str, float]]:
    """
    Confianza embedding similar.
    """
    if not embedding_neighbors:
        return None
    
    folder_votes = {}
    for neighbor_path in embedding_neighbors[:3]:  # Top 3
        for m in meta:
            if m['img'] in os.path.basename(neighbor_path):
                folder = m['folder']
                folder_votes[folder] = folder_votes.get(folder, 0) + 1
    
    if folder_votes:
        top_folder = max(folder_votes, key=folder_votes.get)
        conf = folder_votes[top_folder] / 3.0
        return top_folder, conf
    return None

def move_image(path: str, output_dir: str, folder: str, img: str, index: ImageIndex, meta: list, progress_hook=None, method: str = 'manual', confidence: float = 1.0) -> Optional[str]:
    """
    Mueve SOLO si confident. Embedding ANTES move.
    """
    try:
        vec = get_embedding(path)  # ANTES move!
        safe_folder = sanitize_name(folder)
        dest_dir = os.path.join(output_dir, safe_folder)
        os.makedirs(dest_dir, exist_ok=True)
        safe_img = sanitize_name(img)
        dest_path = os.path.join(dest_dir, safe_img)
        
        # Add to index
        if vec is not None:
            index.add(vec, dest_path)
            meta.append({"img": img, "folder": folder, "method": method, "confidence": confidence})
        
        shutil.move(path, dest_path)
        
        # Learning + DB
        learning_path = os.path.join(output_dir, "learning.json")
        learning = {}
        if os.path.exists(learning_path):
            with open(learning_path, 'r', encoding='utf-8') as f:
                learning = json.load(f)
        learning[img] = folder
        with open(learning_path, 'w', encoding='utf-8') as f:
            json.dump(learning, f, ensure_ascii=False, indent=2)
        
        db_path = os.path.join(output_dir, 'animes.db')
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT OR IGNORE INTO VISTOS (NOMBRE, IMAGEN, SCORE) VALUES (?, ?, ?)", 
                    (safe_folder, safe_img, confidence))
        conn.commit()
        conn.close()
        
        if progress_hook:
            progress_hook(f"MOVIDA {img} → {folder} [{method}:{confidence:.1f}]")
        return dest_path
    except Exception as e:
        logging.error(f"Error moviendo {img}: {e}")
        return None

def organize_images(excel, image_dir, output_dir, progress_hook=None, interactive=False, conf_threshold=0.8, ai_first=False) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    CONF_THRESHOLD = 0.8 (para IA como fallback).
    Pendings NO se mueven.
    Primero actualiza BD desde Excel, luego crea carpetas desde BD.
    """
    logging.basicConfig(level=logging.INFO)

    def model_progress(info):
        if progress_hook:
            progress_hook('ia_progress: ' + str(info))

    # Paths
    excel = os.path.abspath(excel)
    image_dir = os.path.abspath(image_dir)
    output_dir = os.path.abspath(output_dir)

    # === PRIMERO: Actualizar BD desde Excel ===
    if progress_hook:
        progress_hook("Actualizando base de datos desde Excel...")

    # Ejecutar script de creación/actualización de BD
    script_dir = os.path.dirname(os.path.dirname(__file__))
    db_script = os.path.join(script_dir, "db_create.sh")
    if os.path.exists(db_script):
        try:
            subprocess.run(["bash", db_script], check=True, cwd=script_dir,
                         capture_output=True, text=True)
            if progress_hook:
                progress_hook("Base de datos actualizada correctamente")
        except subprocess.CalledProcessError as e:
            if progress_hook:
                progress_hook(f"Error actualizando BD: {e}")
            # Continuar con BD existente si falla

    # === SEGUNDO: Leer nombres desde BD ===
    db_path = os.path.join(os.path.dirname(excel), "animes.db")
    all_names = set()

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Obtener solo la tabla de animes vistos
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ANIMES_VISTOS'")
            tables = cursor.fetchall()

            for table_name, in tables:
                try:
                    cursor.execute(f'SELECT title FROM "{table_name}"')
                    titles = cursor.fetchall()
                    for title, in titles:
                        if title:
                            all_names.add(title.upper())
                except sqlite3.Error:
                    continue  # Saltar tablas con problemas

            conn.close()
            if progress_hook:
                progress_hook(f"Encontrados {len(all_names)} títulos en BD")
        except sqlite3.Error as e:
            if progress_hook:
                progress_hook(f"Error leyendo BD: {e}. Usando Excel como respaldo.")
            # Fallback: leer del Excel si falla BD
            df = pd.read_excel(excel)
            for col in df.columns:
                all_names.update(df[col].dropna().astype(str).str.strip().str.upper())
    else:
        if progress_hook:
            progress_hook("BD no encontrada. Leyendo desde Excel.")
        # Fallback: leer del Excel
        df = pd.read_excel(excel)
        for col in df.columns:
            all_names.update(df[col].dropna().astype(str).str.strip().str.upper())

    all_names_lower = set([name.lower() for name in all_names])

    # === LIMPIEZA PREVIA: Eliminar carpetas no válidas y devolver imágenes ===
    if progress_hook:
        progress_hook("Verificando carpetas existentes...")

    if os.path.exists(output_dir):
        existing_folders = []
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                existing_folders.append(item)

        folders_removed = 0
        images_moved_back = 0

        for folder_name in existing_folders:
            folder_path = os.path.join(output_dir, folder_name)
            folder_name_upper = folder_name.upper()

            # Verificar si la carpeta corresponde a un anime visto
            if folder_name_upper not in all_names:
                if progress_hook:
                    progress_hook(f"Eliminando carpeta no válida: {folder_name}")

                # Mover todas las imágenes de vuelta a la carpeta original
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in IMAGE_EXT):
                        # Mover de vuelta a la carpeta original
                        dest_path = os.path.join(image_dir, file)
                        try:
                            shutil.move(file_path, dest_path)
                            images_moved_back += 1
                            if progress_hook:
                                progress_hook(f"Imagen movida de vuelta: {file}")
                        except Exception as e:
                            if progress_hook:
                                progress_hook(f"Error moviendo {file}: {e}")

                # Eliminar la carpeta vacía
                try:
                    os.rmdir(folder_path)
                    folders_removed += 1
                    if progress_hook:
                        progress_hook(f"Carpeta eliminada: {folder_name}")
                except OSError as e:
                    if progress_hook:
                        progress_hook(f"Error eliminando carpeta {folder_name}: {e}")

        if progress_hook and (folders_removed > 0 or images_moved_back > 0):
            progress_hook(f"Limpieza completada: {folders_removed} carpetas eliminadas, {images_moved_back} imágenes movidas de vuelta")

    # Crear carpetas desde BD
    for a in all_names:
        os.makedirs(os.path.join(output_dir, sanitize_name(str(a))), exist_ok=True)

    # Learning
    learning_path = os.path.join(output_dir, "learning.json")
    learning = {}
    if os.path.exists(learning_path):
        with open(learning_path, "r", encoding="utf-8") as f:
            learning = json.load(f)

    # Index (existente)
    index_path = os.path.join(output_dir, "embeddings.index")
    meta_path = os.path.join(output_dir, "embeddings_meta.json")
    index = ImageIndex()
    meta = []
    if os.path.exists(index_path) and os.path.exists(meta_path):
        index.load(index_path)
        with open(meta_path, "r") as f:
            meta = json.load(f)

    moved_list = []
    pending_list = []
    errors = []

    imgs = [f for f in os.listdir(image_dir) if any(f.lower().endswith(e) for e in IMAGE_EXT)]
    total = len(imgs)
    processed = 0
    
    for img in imgs:
        path = os.path.join(image_dir, img)
        img_base = os.path.splitext(img)[0]
        decision = {'img': img, 'path': path, 'base': img_base, 'options': []}
        
        processed += 1
        if progress_hook:
            progress_hook(f"Procesando {processed}/{total}: {img}")
        
        moved = False
        
        # 1. LEARNING (100%)
        if img in learning:
            dest = move_image(path, output_dir, learning[img], img, index, meta, progress_hook, 'learning', 1.0)
            if dest:
                decision.update({'dest': dest, 'method': 'learning', 'confidence': 1.0})
                moved_list.append(decision)
            moved = True
        
        # 2. NAME_PARTS (70%+)
        if not moved:
            match = match_name_parts_confidence(img_base, all_names)
            if match:
                folder, conf = match
                if conf >= 0.7:  # Reducido de 0.8
                    dest = move_image(path, output_dir, folder, img, index, meta, progress_hook, 'name_parts', conf)
                    if dest:
                        decision.update({'dest': dest, 'method': 'name_parts', 'confidence': conf})
                        moved_list.append(decision)
                    moved = True
        
        # 3. EXACT (100%)
        if not moved:
            norm_img = normalise_image_name(img_base)
            for folder in all_names:
                if norm_img == folder:
                    dest = move_image(path, output_dir, folder, img, index, meta, progress_hook, 'exact', 1.0)
                    if dest:
                        decision.update({'dest': dest, 'method': 'exact', 'confidence': 1.0})
                        moved_list.append(decision)
                    moved = True
                    break
        
        # 4. SIMILAR EMBEDDING (>0.75)
        if not moved:
            vec = get_embedding(path)
            if vec is not None and meta:
                neighbors = index.search(vec, k=5)  # Más vecinos para mejor matching
                sim_match = get_similarity_confidence(neighbors, meta)
                if sim_match:
                    folder_sim, conf_sim = sim_match
                    if conf_sim >= 0.75:  # Reducido de 0.85
                        dest = move_image(path, output_dir, folder_sim, img, index, meta, progress_hook, 'similar', conf_sim)
                        if dest:
                            decision.update({'dest': dest, 'method': 'similar', 'confidence': conf_sim})
                            moved_list.append(decision)
                        moved = True
        
        # 5. IA (CLIP) como fallback - siempre se ejecuta si otros métodos fallaron
        if not moved:
            try:
                anime, score = predict_anime(path, list(all_names), model_progress)
                if score >= 0.8:  # Threshold más bajo para IA como fallback
                    dest = move_image(path, output_dir, str(anime).strip().upper(), img, index, meta, progress_hook, 'clip', score)
                    if dest:
                        decision.update({'dest': dest, 'method': 'clip', 'confidence': score})
                        moved_list.append(decision)
            except Exception as e:
                errors.append(f"{img}: IA error - {str(e)}")
    
    # Save
    index.save(index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    if progress_hook:
        progress_hook(f"COMPLETADO: {len(moved_list)} movidas, {len(pending_list)} pendientes (quedan original)")
    
    return moved_list, pending_list, errors

if __name__ == "__main__":
    print("Core organizer listo - modo safe.")
