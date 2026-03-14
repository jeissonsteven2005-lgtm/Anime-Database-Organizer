import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import os

from anime_organizer_ai import run_organizer, normalise_image_name


def start_gui():

    root = tk.Tk()
    root.title("Anime Organizer AI")
    root.geometry("700x400")

    excel_var = tk.StringVar()
    images_var = tk.StringVar()
    output_var = tk.StringVar(value=os.path.expanduser("~/Escritorio/filtrada"))
    modo_var = tk.StringVar(value="mover")
    ignore_var = tk.StringVar(value="PORTADA,LATINO,DESUPORTADA")

    sample_var = tk.StringVar()
    result_var = tk.StringVar(value="Normalizado:")

    progress_var = tk.StringVar(value="Esperando...")

    def browse_excel():
        path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if path:
            excel_var.set(path)

    def browse_images():
        path = filedialog.askdirectory()
        if path:
            images_var.set(path)

    def browse_output():
        path = filedialog.askdirectory()
        if path:
            output_var.set(path)

    def update_sample(*args):

        nm = sample_var.get()

        ignore_words = [
            w.strip().upper()
            for w in ignore_var.get().split(",")
            if w.strip()
        ]

        norm = normalise_image_name(nm, ignore_words)

        result_var.set(f"Normalizado: {norm}")

    sample_var.trace_add("write", update_sample)

    def run():

        if not excel_var.get():
            messagebox.showwarning("Error", "Selecciona Excel")
            return

        if not images_var.get():
            messagebox.showwarning("Error", "Selecciona carpeta de imágenes")
            return

        progress_var.set("Procesando...")

        def task():

            try:

                run_organizer(
                    excel_var.get(),
                    images_var.get(),
                    output_var.get(),
                    modo_var.get(),
                    ignore_var.get(),
                )

                progress_var.set("Proceso completado")

            except Exception as e:

                progress_var.set("Error")

                messagebox.showerror("Error", str(e))

        threading.Thread(target=task).start()

    tk.Label(root, text="Excel").grid(row=0, column=0)
    tk.Entry(root, textvariable=excel_var, width=50).grid(row=0, column=1)
    tk.Button(root, text="...", command=browse_excel).grid(row=0, column=2)

    tk.Label(root, text="Carpeta imágenes").grid(row=1, column=0)
    tk.Entry(root, textvariable=images_var, width=50).grid(row=1, column=1)
    tk.Button(root, text="...", command=browse_images).grid(row=1, column=2)

    tk.Label(root, text="Salida").grid(row=2, column=0)
    tk.Entry(root, textvariable=output_var, width=50).grid(row=2, column=1)
    tk.Button(root, text="...", command=browse_output).grid(row=2, column=2)

    tk.Label(root, text="Modo").grid(row=3, column=0)
    tk.OptionMenu(root, modo_var, "mover", "copiar").grid(row=3, column=1)

    tk.Label(root, text="Palabras ignoradas").grid(row=4, column=0)
    tk.Entry(root, textvariable=ignore_var, width=50).grid(row=4, column=1)

    tk.Label(root, text="Ejemplo nombre").grid(row=5, column=0)
    tk.Entry(root, textvariable=sample_var, width=50).grid(row=5, column=1)

    tk.Label(root, textvariable=result_var).grid(row=6, column=1)

    tk.Button(root, text="Ejecutar", command=run).grid(row=7, column=1)

    tk.Label(root, textvariable=progress_var).grid(row=8, column=1)

    root.mainloop()


if __name__ == "__main__":
    start_gui()