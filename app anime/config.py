if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en config.py:\n{e}\n\n{traceback.format_exc()}")
DEFAULT_IGNORE = [
    "PORTADA",
    "LATINO",
    "SUB",
    "HD",
    "DESUPORTADA"
]

IMAGE_EXT = [".jpg", ".jpeg", ".png", ".webp"]