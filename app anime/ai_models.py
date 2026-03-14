if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en ai_models.py:\n{e}\n\n{traceback.format_exc()}")


import torch
import open_clip
from PIL import Image
import logging
from typing import List, Tuple, Optional, Callable
import os
import threading
import subprocess

# Cargar modelo y tokenizer una sola vez (singleton)
_MODEL = None
_PREPROCESS = None
_TOKENIZER = None
_MODEL_LOCK = threading.Lock()

def get_model(progress_callback: Optional[Callable[[int], None]] = None):
    # Acelera descargas usando HF_TOKEN si no está presente
    if not os.environ.get("HF_TOKEN"):
        try:
            # Intenta login automático si huggingface-cli está instalado
            subprocess.run(["huggingface-cli", "login", "--token"], check=False)
        except Exception:
            pass
    """
    Carga el modelo open_clip usando caché local. Si el modelo no está descargado, lo descarga y muestra progreso.
    Si ocurre un error, lo reporta claramente.
    progress_callback: función opcional para reportar progreso de descarga (recibe porcentaje de 0 a 100).
    """
    global _MODEL, _PREPROCESS, _TOKENIZER
    with _MODEL_LOCK:
        if _MODEL is not None and _PREPROCESS is not None and _TOKENIZER is not None:
            return _MODEL, _PREPROCESS, _TOKENIZER

        cache_dir = os.path.expanduser("~/.cache/open_clip")
        os.makedirs(cache_dir, exist_ok=True)
        model_path = os.path.join(cache_dir, "open_clip_pytorch_model.bin")

        # Verifica permisos de lectura/escritura
        if not os.access(cache_dir, os.W_OK | os.R_OK):
            logging.error(f"Permisos insuficientes en la carpeta de caché: {cache_dir}")
            return None, None, None


        # Siempre usar el nombre del checkpoint recomendado
        try:
            _MODEL, _, _PREPROCESS = open_clip.create_model_and_transforms(
                "ViT-B-32",
                pretrained="laion2b_s34b_b79k",
                cache_dir=cache_dir
            )
            _TOKENIZER = open_clip.get_tokenizer("ViT-B-32")
            _MODEL.eval()
            logging.info("Modelo ViT-B-32 cargado con pesos preentrenados laion2b_s34b_b79k.")
            return _MODEL, _PREPROCESS, _TOKENIZER
        except Exception as e:
            logging.error(f"Error al cargar el modelo open_clip: {e}\n\nSi tienes problemas de red, descarga manualmente el modelo desde Hugging Face y colócalo en {cache_dir}.")
            return None, None, None

        # Parchear el método de descarga para mostrar progreso si se provee callback
        def _progress_hook(bytes_downloaded, total_bytes):
            if progress_callback and total_bytes > 0:
                percent = int(bytes_downloaded * 100 / total_bytes)
                progress_callback(percent)

        try:
            import huggingface_hub
            huggingface_hub.utils._tqdm.tqdm = lambda *a, **kw: None
            huggingface_hub.file_download._progress_hook = _progress_hook
            # Si hay token, lo usa
            if os.environ.get("HF_TOKEN"):
                huggingface_hub.login(token=os.environ["HF_TOKEN"])
        except Exception as e:
            logging.warning(f"No se pudo inicializar huggingface_hub: {e}")

        try:
            _MODEL, _, _PREPROCESS = open_clip.create_model_and_transforms(
                "ViT-B-32",
                pretrained="laion2b_s34b_b79k",
                cache_dir=cache_dir
            )
            _TOKENIZER = open_clip.get_tokenizer("ViT-B-32")
            _MODEL.eval()
            logging.info("Modelo descargado y cargado con pesos preentrenados.")
        except Exception as e:
            logging.error(f"Error al cargar el modelo open_clip: {e}\n\nSi tienes problemas de red, descarga manualmente el modelo desde Hugging Face y colócalo en {cache_dir}.")
            return None, None, None
        return _MODEL, _PREPROCESS, _TOKENIZER

def get_embedding(image_path: str) -> Optional[torch.Tensor]:
    model, preprocess, _ = get_model()
    try:
        image = preprocess(Image.open(image_path)).unsqueeze(0)
        with torch.no_grad():
            features = model.encode_image(image)
        return features.cpu().numpy()
    except Exception as e:
        logging.error(f"Error obteniendo embedding de {image_path}: {e}")
        return None

def predict_anime(image_path: str, anime_list: List[str], return_probs: bool = False, progress_callback: Optional[Callable[[int], None]] = None) -> Tuple[str, float]:
    model, preprocess, tokenizer = get_model(progress_callback=progress_callback)
    if model is None or preprocess is None or tokenizer is None:
        return {"error": "open_clip_model_missing"}, 0.0
    try:
        image = preprocess(Image.open(image_path)).unsqueeze(0)
        text = tokenizer(list(anime_list))
        with torch.no_grad():
            image_features = model.encode_image(image)
            text_features = model.encode_text(text)
            probs = (image_features @ text_features.T).softmax(dim=-1)
        best = probs.argmax().item()
        if return_probs:
            return list(anime_list)[best], probs[0][best].item(), probs[0].cpu().numpy()
        return list(anime_list)[best], probs[0][best].item()
    except Exception as e:
        logging.error(f"Error en predicción para {image_path}: {e}")
        return {"error": str(e)}, 0.0

def batch_get_embeddings(image_paths: List[str]) -> List[Optional[torch.Tensor]]:
    model, preprocess, _ = get_model()
    images = []
    for path in image_paths:
        try:
            images.append(preprocess(Image.open(path)).unsqueeze(0))
        except Exception as e:
            logging.error(f"Error procesando {path}: {e}")
            images.append(None)
    batch = [img for img in images if img is not None]
    if not batch:
        return [None] * len(image_paths)
    batch_tensor = torch.cat(batch, dim=0)
    with torch.no_grad():
        features = model.encode_image(batch_tensor)
    out = []
    idx = 0
    for img in images:
        if img is not None:
            out.append(features[idx].cpu().numpy())
            idx += 1
        else:
            out.append(None)
    return out