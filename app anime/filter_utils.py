import re
from typing import List, Set, Optional

DEFAULT_IGNORE = ["PORTADA", "LATINO", "DESU", "SUB", "DUB", "OVA", "MOVIE", "EP"]

def normalise_image_name(name: str, ignore_words=None) -> str:
    """
    Normaliza nombre de imagen para filtrado: reemplaza _ por espacio, ignora palabras,
    quita números finales, upper, strip.
    """
    if ignore_words is None:
        ignore_words = DEFAULT_IGNORE
    s = name.replace("_", " ")
    s = s.upper()
    # Ignorar palabras (más largas primero)
    for w in sorted(ignore_words, key=len, reverse=True):
        s = s.replace(w.upper(), "")
    s = re.sub(r"\\d+$", "", s)
    s = re.sub(r"\\s+", " ", s).strip()
    return s

def split_words(name: str) -> List[str]:
    """
    Divide nombre normalizado en palabras (izquierda a derecha).
    """
    norm = normalise_image_name(name)
    return [w.strip() for w in norm.split() if w.strip()]

def generate_options_sequential(img_name: str, all_names: Set[str], max_options: int = 3) -> List[str]:
    """
    Filtrado secuencial por palabras (izq->der) hasta <= max_options.
    Toma palabras del nombre imagen -> filtra carpetas coincidentes acumulativamente.
    """
    words = split_words(img_name)
    if not words:
        return list(all_names)[:max_options]  # Fallback
    
    candidates = set(all_names)
    for word in words:
        new_candidates = set()
        for name in candidates:
            if word in name.upper():
                new_candidates.add(name)
        candidates = new_candidates
        if len(candidates) <= max_options:
            break
    
    options = sorted(list(candidates))[:max_options]
    if len(options) == 0:
        # Fallback fuzzy si vacío
        from difflib import get_close_matches
        norm_img = normalise_image_name(img_name)
        options = get_close_matches(norm_img, list(all_names), n=max_options, cutoff=0.6)
    return options

def suggest_names(norm: str, valid_names: Set[str], learning: dict = None) -> List[str]:
    """
    Sugerencias: learning + exacto/contención + fuzzy.
    """
    from difflib import get_close_matches
    suggestions = []
    if learning and norm:
        for key, val in learning.items():
            if norm == key or key in norm or norm in key:
                suggestions.append(val)
        closers = get_close_matches(norm, list(learning.keys()), n=3, cutoff=0.6)
        for k in closers:
            v = learning.get(k)
            if v and v not in suggestions:
                suggestions.append(v)
    for candidate in valid_names:
        if norm in candidate.upper() or candidate.upper() in norm:
            if candidate not in suggestions:
                suggestions.append(candidate)
    closers = get_close_matches(norm, list(valid_names), n=5, cutoff=0.6)
    for c in closers:
        if c not in suggestions:
            suggestions.append(c)
    return suggestions[:5]

