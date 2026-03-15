import os
import sys
from PySide6.QtWidgets import (QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QWidget, QTabWidget, QListWidget, QProgressBar, QMessageBox, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from organizer_core import organize_images
from collections import Counter

class Worker(QThread):
    progress = Signal(str)
    current_img = Signal(str)
    stats_update = Signal(dict)
    finished = Signal(object, object, object)
    
    def __init__(self, excel, images, output, ai_first):
        super().__init__()
        self.excel = excel
        self.images = images
        self.output = output
        self.ai_first = ai_first
        
    def run(self):
        try:
            moved, pending, errors = organize_images(self.excel, self.images, self.output, 
                                                   self.progress.emit, False, 0.9, self.ai_first)
            self.finished.emit(moved, pending, errors)
        except Exception as e:
            self.progress.emit(f"ERROR: {str(e)}")

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime AI Organizer - Modo SAFE")
        self.setGeometry(100, 100, 1000, 600)
        self.moved_list = []
        self.pending_data = []
        self.errors = []
        self.current_folder_stats = {}
        self.worker = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # === CONFIG ===
        config = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("<h1>🎌 Organizador SAFE</h1><h3>Solo mueve confident (>90%). Pendings quedan original.</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Paths
        row1 = QHBoxLayout()
        self.excel_path = QLineEdit('"lista de animes actualización.xlsx"')
        row1.addWidget(QLabel("📊 Excel:"))
        row1.addWidget(self.excel_path)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.images_path = QLineEdit('"anime/"')
        row2.addWidget(QLabel("🖼 Imágenes:"))
        row2.addWidget(self.images_path)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.output_path = QLineEdit('"filtrar/"')
        row3.addWidget(QLabel("📁 Salida:"))
        row3.addWidget(self.output_path)
        layout.addLayout(row3)

        # Options
        self.ai_first = QCheckBox("🔥 IA primero (lento)")
        self.ai_first.setChecked(False)
        layout.addWidget(self.ai_first)

        # Run
        self.btn_run = QPushButton("🚀 ORGANIZAR")
        self.btn_run.clicked.connect(self.start_organize)
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px; padding: 15px; border-radius: 10px;")
        layout.addWidget(self.btn_run)

        # Progress
        self.progress_label = QLabel("Listo")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.current_img_label = QLabel("Imagen actual: -")
        self.current_img_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.current_img_label)

        config.setLayout(layout)
        self.tabs.addTab(config, "⚙️ Config")

        # === PROCESANDO (real-time) ===
        proc_widget = QWidget()
        p_layout = QVBoxLayout()
        self.proc_list = QListWidget()
        p_layout.addWidget(QLabel("📋 Proceso LIVE:"))
        p_layout.addWidget(self.proc_list)
        proc_widget.setLayout(p_layout)
        self.tabs.addTab(proc_widget, "🔄 Procesando")

        # === RESULTADOS STATS ===
        results_widget = QWidget()
        r_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        r_layout.addWidget(QLabel("📊 ESTADÍSTICAS por CARPETA:"))
        r_layout.addWidget(self.results_text)
        results_widget.setLayout(r_layout)
        self.tabs.addTab(results_widget, "📊 Resultados")

        # === PENDIENTES ===
        pending_widget = QWidget()
        pend_layout = QVBoxLayout()
        self.pending_list = QListWidget()
        self.pending_list.itemClicked.connect(self.show_pending_detail)
        self.pending_detail = QLabel("Selecciona...")
        pend_layout.addWidget(QLabel("⏳ PENDIENTES (quedan original):"))
        pend_layout.addWidget(self.pending_list)
        pend_layout.addWidget(self.pending_detail)
        pending_widget.setLayout(pend_layout)
        self.tabs.addTab(pending_widget, "⏳ Pendientes")

    def start_organize(self):
        excel = self.excel_path.text().strip('"')
        images = self.images_path.text().strip('"')
        output = self.output_path.text().strip('"')
        
        if not os.path.isfile(excel):
            QMessageBox.critical(self, "Error", f"Excel no encontrado: {excel}")
            return
        if not os.path.isdir(images):
            QMessageBox.critical(self, "Error", f"Imágenes no encontradas: {images}")
            return
        os.makedirs(output, exist_ok=True)

        self.btn_run.setEnabled(False)
        self.proc_list.clear()
        self.results_text.clear()
        self.pending_list.clear()
        self.pending_data.clear()
        self.moved_list = []
        self.pending_data = []

        self.worker = Worker(excel, images, output, self.ai_first.isChecked())
        self.worker.progress.connect(self.update_progress)
        self.worker.current_img.connect(self.update_current_img)
        self.worker.stats_update.connect(self.update_stats)
        self.worker.finished.connect(self.on_finish)
        self.worker.start()
        
        self.progress_label.setText("Iniciando...")
        self.tabs.setCurrentIndex(1)  # Procesando

    def update_progress(self, msg):
        self.progress_label.setText(msg)
        self.proc_list.addItem(msg)
        self.proc_list.scrollToBottom()

    def update_current_img(self, img):
        self.current_img_label.setText(f"🔍 Imagen: {img}")

    def update_stats(self, stats):
        self.current_folder_stats = stats
        stats_text = "CARPETAS:\n"
        for folder, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            stats_text += f"  {folder}: {count} imgs\n"
        self.results_text.setText(stats_text)

    def on_finish(self, moved, pending, errors):
        self.moved_list = moved
        self.pending_data = pending
        self.errors = errors
        
        # Final stats
        folder_counts = Counter([d.get('folder', d.get('dest', '').split(os.sep)[-2] if d.get('dest') else '') for d in moved])
        self.update_stats(folder_counts)
        
        self.progress_label.setText(f"✅ TERMINADO | Movidas: {len(moved)} | Pendientes: {len(pending)}")
        self.progress_bar.setVisible(False)
        self.btn_run.setEnabled(True)
        self.tabs.setCurrentIndex(2)  # Resultados
        
        self.pending_list.addItems([f"{p['img']} - {', '.join(p.get('options', [])[:3])}" for p in self.pending_data])
        
        if errors:
            self.proc_list.addItems([f"ERROR: {e}" for e in errors[-10:]])

    def show_pending_detail(self, item):
        idx = self.pending_list.row(item)
        p = self.pending_data[idx] if idx < len(self.pending_data) else {}
        opts = ', '.join(p.get('options', [])[:5])
        self.pending_detail.setText(f"Archivo: {p.get('img', 'N/A')}\nSugerencias: {opts}")

    # Pickers (mantenidos)
    def pick_excel(self):
        pass  # Implementar si necesario
    def pick_images(self):
        pass
    def pick_output(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec())
