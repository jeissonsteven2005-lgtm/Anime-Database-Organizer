if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en vector_index.py:\n{e}\n\n{traceback.format_exc()}")
import faiss
import numpy as np
import logging
import os

class ImageIndex:
    def __init__(self, dim=512):
        self.index = faiss.IndexFlatL2(dim)
        self.paths = []
        self.embeddings = []

    def add(self, vec, path):
        try:
            if vec.ndim == 1:
                vec = vec.reshape(1, -1)
            self.index.add(vec.astype(np.float32))
            self.paths.append(path)
            self.embeddings.append(vec)
        except Exception as e:
            logging.error(f"Error añadiendo embedding para {path}: {e}")

    def search(self, vec, k=5):
        try:
            if vec.ndim == 1:
                vec = vec.reshape(1, -1)
            D, I = self.index.search(vec.astype(np.float32), k)
            return [self.paths[i] for i in I[0] if i < len(self.paths)]
        except Exception as e:
            logging.error(f"Error en búsqueda FAISS: {e}")
            return []

    def save(self, path):
        try:
            faiss.write_index(self.index, path)
        except Exception as e:
            logging.error(f"Error guardando índice FAISS: {e}")

    def load(self, path):
        if os.path.exists(path):
            try:
                self.index = faiss.read_index(path)
            except Exception as e:
                logging.error(f"Error cargando índice FAISS: {e}")