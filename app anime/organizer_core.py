import re
import os
import shutil
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
    \"\"\"
    Reemplaza caracteres no validos para carpetas.
    \"\"\"
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", name)
    return sanitized[:255]

def match_name_parts_confidence(img_base: str, all_names: set, min_conf=0.8) -> Optional[Tuple[str, float]]:
    \"\"\"
    Matching jerárquico con confianza.
    Retorna (folder, confidence) si > min_conf.
    \"\"\"
    words = img_base.replace('_', ' ').split()
    candidates = set(all_names)
    
    word_matches = 0
    total_words = len([w for w in words if w.strip()])
    
    for word in words:
        word_upper = word.strip().upper()
        if not word_upper:
            continue
        new_candidates = set()
        for folder in candidates:
            if word_upper in folder.upper():
                new_candidates.add(folder)
                word_matches += 1
        candidates = new_candidates
        if len(candidates) == 1:
            conf = word_matches / max(total_words, 1)
            if conf >= min_conf:
                return list(candidates)[0], conf
    
    return None

def get_similarity_confidence(embedding_neighbors: list, meta: list) -> Optional[Tuple[str, float]]:
    \"\"\"
    Confianza embedding similar.
    \"\"\"
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
    \"\"\"
    Mueve SOLO si confident. Embedding ANTES move.
    \"\"\"
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
        
        # Learning + DB (igual)
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

def organize_images(excel, image_dir, output_dir, progress_hook=None, interactive=False, conf_threshold=0.9, ai_first=False) -> Tuple[List[Dict], List[Dict], List[str]]:
    \"\"\"
    CONF_THRESHOLD = 0.9 (solo mover confident).
    Pendings NO se mueven.
    \"\"\"
    logging.basicConfig(level=logging.INFO)
    
    def model_progress(info):
        if progress_hook:
            progress_hook('ia_progress: ' + str(info))
    
    # Paths
    excel = os.path.abspath(excel)
    image_dir = os.path.abspath(image_dir)
    output_dir = os.path.abspath(output_dir)

    # Excel + all_names
    df = pd.read_excel(excel)
    all_names = set()
    for col in df.columns:
        all_names.update(df[col].dropna().astype(str).str.strip().str.upper())
    all_names_lower = set([name.lower() for name in all_names])
    
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
        
        # 2. NAME_PARTS (80%+)
        if not moved:
            match = match_name_parts_confidence(img_base, all_names_lower)
            if match:
                folder, conf = match
                if conf >= 0.8:
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
        
        # 4. SIMILAR EMBEDDING (>0.85)
        if not moved:
            vec = get_embedding(path)
            if vec is not None and meta:
                neighbors = index.search(vec, k=3)
                sim_match = get_similarity_confidence(neighbors, meta)
                if sim_match:
                    folder_sim, conf_sim = sim_match
                    if conf_sim >= 0.85:
                        dest = move_image(path, output_dir, folder_sim, img, index, meta, progress_hook, 'similar', conf_sim)
                        if dest:
                            decision.update({'dest': dest, 'method': 'similar', 'confidence': conf_sim})
                            moved_list.append(decision)
                        moved = True
        
        # PENDING (NO MOVE!)
        if not moved:
            decision['method'] = 'pending'
            decision['options'] = generate_options_sequential(img_base, all_names)
            pending_list.append(decision)
            if progress_hook:
                progress_hook(f"PENDING {img} - opciones: {len(decision['options'])}")
        
        # IA solo si ai_first=True y no moved
        if not moved and ai_first:
            try:
                anime, score = predict_anime(path, list(all_names), model_progress)
                if score >= conf_threshold:
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

