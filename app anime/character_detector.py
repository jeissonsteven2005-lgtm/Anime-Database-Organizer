if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en character_detector.py:\n{e}\n\n{traceback.format_exc()}")
from ultralytics import YOLO
import logging

_MODEL = None
_CLASS_NAMES = None

def get_model():
    global _MODEL, _CLASS_NAMES
    if _MODEL is None:
        _MODEL = YOLO("yolov8n.pt")
        # Cargar nombres de clase si están disponibles
        try:
            _CLASS_NAMES = _MODEL.names
        except Exception:
            _CLASS_NAMES = None
    return _MODEL, _CLASS_NAMES

def detect_characters(image_path, conf_threshold=0.3):
    model, class_names = get_model()
    try:
        results = model(image_path)
        chars = []
        for r in results:
            for box in r.boxes:
                if hasattr(box, 'conf') and box.conf.item() < conf_threshold:
                    continue
                cls_id = int(box.cls.item()) if hasattr(box.cls, 'item') else int(box.cls)
                name = class_names[cls_id] if class_names and cls_id < len(class_names) else str(cls_id)
                chars.append(name)
        return chars
    except Exception as e:
        logging.error(f"Error detectando personajes en {image_path}: {e}")
        return []