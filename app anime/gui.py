import os
import sys
import shutil
import sqlite3
from PySide6.QtWidgets import (QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QWidget, QTabWidget, QListWidget, QProgressBar, QMessageBox, QCheckBox, QTextEdit, QFrame, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush
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
        self.setWindowTitle("🎌 Anime AI Organizer Pro - Modo SAFE")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(1000, 600)

        # Aplicar tema moderno
        self.apply_modern_theme()

        self.moved_list = []
        self.pending_data = []
        self.errors = []
        self.current_folder_stats = {}
        self.worker = None

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #3498db;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 12px 20px;
                margin-right: 2px;
                border-radius: 8px 8px 0 0;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6b, stop:1 #ee5a24);
                color: white;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
            }
        """)
        self.setCentralWidget(self.tabs)

        self.create_config_tab()
        self.create_processing_tab()
        self.create_results_tab()
        self.create_pending_tab()
        self.create_rename_tab()

    def apply_modern_theme(self):
        """Aplica un tema moderno con gradientes y colores atractivos"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }

            QLabel {
                color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QLabel[h1="true"] {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }

            QLabel[h3="true"] {
                color: #ecf0f1;
                font-size: 14px;
                font-weight: 300;
            }

            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #2c3e50;
            }

            QLineEdit:focus {
                border-color: #3498db;
                background: white;
            }

            QCheckBox {
                color: #ecf0f1;
                font-size: 14px;
                font-weight: 500;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #bdc3c7;
                background: rgba(255, 255, 255, 0.9);
            }

            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6b, stop:1 #ee5a24);
                border-color: #e74c3c;
            }

            QListWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                selection-background-color: #3498db;
                alternate-background-color: #f8f9fa;
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }

            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                color: white;
            }

            QTextEdit {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }

            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                background: rgba(255, 255, 255, 0.9);
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6b, stop:1 #ee5a24);
                border-radius: 6px;
            }
        """)

    def create_config_tab(self):
        """Crea la pestaña de configuración con diseño moderno"""
        config = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header con gradiente
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:1 #ee5a24);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout()

        title = QLabel("🎌 Anime AI Organizer Pro")
        title.setProperty("h1", True)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Organizador inteligente con IA - Modo SAFE")
        subtitle.setProperty("h3", True)
        subtitle.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        # Grupo de configuración
        config_group = QGroupBox("⚙️ Configuración de Archivos")
        config_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #3498db;
                font-weight: bold;
            }
        """)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)

        # Excel path
        excel_layout = QHBoxLayout()
        excel_label = QLabel("📊 Archivo Excel:")
        excel_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self.excel_path = QLineEdit('"lista de animes actualización.xlsx"')
        self.excel_path.setStyleSheet("font-size: 12px;")
        excel_layout.addWidget(excel_label)
        excel_layout.addWidget(self.excel_path)
        config_layout.addLayout(excel_layout)

        # Images path
        images_layout = QHBoxLayout()
        images_label = QLabel("🖼️ Carpeta Imágenes:")
        images_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.images_path = QLineEdit('"anime/"')
        self.images_path.setStyleSheet("font-size: 12px;")
        images_layout.addWidget(images_label)
        images_layout.addWidget(self.images_path)
        config_layout.addLayout(images_layout)

        # Output path
        output_layout = QHBoxLayout()
        output_label = QLabel("📁 Carpeta Salida:")
        output_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        self.output_path = QLineEdit('"filtrar/"')
        self.output_path.setStyleSheet("font-size: 12px;")
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path)
        config_layout.addLayout(output_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Opciones avanzadas
        options_group = QGroupBox("🔧 Opciones Avanzadas")
        options_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #9b59b6;
                font-weight: bold;
            }
        """)
        options_layout = QVBoxLayout()

        self.ai_first = QCheckBox("🔥 Usar IA primero (más preciso pero lento)")
        self.ai_first.setChecked(False)
        self.ai_first.setStyleSheet("QCheckBox { spacing: 10px; }")
        options_layout.addWidget(self.ai_first)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Botón de ejecutar
        self.btn_run = QPushButton("🚀 ¡INICIAR ORGANIZACIÓN!")
        self.btn_run.clicked.connect(self.start_organize)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6b, stop:1 #ee5a24);
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border-radius: 15px;
                border: none;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_run)

        # Botón de renombrar
        self.btn_rename = QPushButton("🔄 ¡RENOMBRAR CARPETAS E IMÁGENES!")
        self.btn_rename.clicked.connect(self.start_rename)
        self.btn_rename.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 12px;
                border: none;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7d3c98, stop:1 #6c3483);
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_rename)

        # Barra de progreso
        progress_group = QGroupBox("📈 Progreso")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #f39c12;
                border-radius: 10px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #f39c12;
                font-weight: bold;
            }
        """)
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("✨ Listo para comenzar")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border-radius: 8px; }")

        self.current_img_label = QLabel("🔍 Imagen actual: -")
        self.current_img_label.setStyleSheet("font-weight: bold; color: #3498db; font-size: 12px;")

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.current_img_label)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        layout.addStretch()
        config.setLayout(layout)

        # Agregar scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(config)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.9);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        self.tabs.addTab(scroll_area, "⚙️ Configuración")

    def create_processing_tab(self):
        """Crea la pestaña de procesamiento en tiempo real"""
        proc_widget = QWidget()
        p_layout = QVBoxLayout()
        p_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        proc_header = QLabel("🔄 Procesamiento en Tiempo Real")
        proc_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        p_layout.addWidget(proc_header)

        # Lista de proceso
        self.proc_list = QListWidget()
        self.proc_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #3498db;
                border-radius: 10px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ecf0f1;
            }
        """)
        p_layout.addWidget(self.proc_list)

        proc_widget.setLayout(p_layout)

        # Agregar scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(proc_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.9);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        self.tabs.addTab(scroll_area, "🔄 Procesando")

    def create_results_tab(self):
        """Crea la pestaña de resultados y estadísticas"""
        results_widget = QWidget()
        r_layout = QVBoxLayout()
        r_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        results_header = QLabel("📊 Estadísticas por Carpeta")
        results_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        r_layout.addWidget(results_header)

        # Lista de carpetas (clickeable)
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_folder_images)
        self.results_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #27ae60;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #2ecc71);
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background: rgba(39, 174, 96, 0.1);
            }
        """)
        r_layout.addWidget(self.results_list)

        # Área para mostrar imágenes de la carpeta seleccionada
        images_header = QLabel("🖼️ Imágenes en la carpeta seleccionada:")
        images_header.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 15px;
            margin-bottom: 5px;
        """)
        r_layout.addWidget(images_header)

        self.folder_images_text = QTextEdit()
        self.folder_images_text.setReadOnly(True)
        self.folder_images_text.setMaximumHeight(200)
        self.folder_images_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #3498db;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.3;
            }
        """)
        # Texto inicial más descriptivo
        self.folder_images_text.setPlainText("💡 Haz clic en cualquier carpeta de la lista superior para ver las imágenes que contiene.\n\nCada carpeta muestra su nombre y el número de imágenes organizadas en ella.")
        r_layout.addWidget(self.folder_images_text)

        results_widget.setLayout(r_layout)

        # Agregar scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(results_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.9);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        self.tabs.addTab(scroll_area, "📊 Resultados")

    def create_pending_tab(self):
        """Crea la pestaña de archivos pendientes"""
        pending_widget = QWidget()
        pend_layout = QVBoxLayout()
        pend_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        pending_header = QLabel("⏳ Archivos Pendientes")
        pending_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        pend_layout.addWidget(pending_header)

        # Lista de pendientes
        self.pending_list = QListWidget()
        self.pending_list.itemClicked.connect(self.show_pending_detail)
        self.pending_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #f39c12;
                border-radius: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
            }
        """)
        pend_layout.addWidget(self.pending_list)

        # Detalles del pendiente seleccionado
        self.pending_detail = QLabel("Selecciona un archivo pendiente para ver detalles...")
        self.pending_detail.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                font-size: 12px;
                color: #2c3e50;
                min-height: 60px;
            }
        """)
        self.pending_detail.setWordWrap(True)
        pend_layout.addWidget(self.pending_detail)

        pending_widget.setLayout(pend_layout)

        # Agregar scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(pending_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.9);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        self.tabs.addTab(scroll_area, "⏳ Pendientes")

    def create_rename_tab(self):
        """Crea la pestaña dedicada para renombrar carpetas e imágenes"""
        rename_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header con gradiente
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout()

        title = QLabel("🔄 Renombrar Carpetas e Imágenes")
        title.setProperty("h1", True)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")

        subtitle = QLabel("Herramienta integrada - También disponible como proceso independiente")
        subtitle.setProperty("h3", True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 12px;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        # Información sobre la funcionalidad
        info_group = QGroupBox("ℹ️ ¿Qué hace esta función?")
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #9b59b6;
                font-weight: bold;
            }
        """)
        info_layout = QVBoxLayout()

        info_text = QLabel(
            "Esta función realiza las siguientes acciones:\n\n"
            "1. 🧹 LIMPIEZA AUTOMÁTICA: Elimina carpetas no válidas y devuelve imágenes al origen\n"
            "2. 📁 Renombra carpetas según los nombres correctos de la base de datos\n"
            "3. 🖼️ Renombra imágenes dentro de cada carpeta como 'NOMBRE_CARPETA # 1.jpg', etc.\n"
            "4. 🔍 Busca coincidencias inteligentes entre nombres existentes y correctos\n"
            "5. ✅ Convierte todos los nombres a MAYÚSCULAS para consistencia\n\n"
            "⚠️ IMPORTANTE: Esta acción modifica los nombres de archivos y carpetas permanentemente.\n\n"
            "💡 También disponible como herramienta independiente: rename_tool.py"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 12px; line-height: 1.5;")
        info_layout.addWidget(info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Configuración de carpeta
        config_group = QGroupBox("⚙️ Configuración")
        config_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #3498db;
                font-weight: bold;
            }
        """)
        config_layout = QVBoxLayout()

        # Output path
        output_layout = QHBoxLayout()
        output_label = QLabel("📁 Carpeta a renombrar:")
        output_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        self.rename_output_path = QLineEdit('"filtrar/"')
        self.rename_output_path.setStyleSheet("font-size: 12px;")
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.rename_output_path)
        config_layout.addLayout(output_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Botón de renombrar
        self.btn_rename = QPushButton("🔄 ¡RENOMBRAR CARPETAS E IMÁGENES!")
        self.btn_rename.clicked.connect(self.start_rename)
        self.btn_rename.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border-radius: 15px;
                border: none;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7d3c98, stop:1 #6c3483);
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_rename)

        # Barra de progreso
        progress_group = QGroupBox("📈 Progreso del Renombrado")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #f39c12;
                border-radius: 10px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #f39c12;
                font-weight: bold;
            }
        """)
        progress_layout = QVBoxLayout()

        self.rename_progress_label = QLabel("✨ Listo para renombrar")
        self.rename_progress_label.setAlignment(Qt.AlignCenter)
        self.rename_progress_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")

        self.rename_progress_bar = QProgressBar()
        self.rename_progress_bar.setVisible(False)
        self.rename_progress_bar.setStyleSheet("QProgressBar { border-radius: 8px; }")

        progress_layout.addWidget(self.rename_progress_label)
        progress_layout.addWidget(self.rename_progress_bar)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        layout.addStretch()
        rename_widget.setLayout(layout)

        # Agregar scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(rename_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.9);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        self.tabs.addTab(scroll_area, "🔄 Renombrar")

    def start_organize(self):
        excel = self.excel_path.text().strip('"')
        images = self.images_path.text().strip('"')
        output = self.output_path.text().strip('"')

        if not os.path.isfile(excel):
            QMessageBox.critical(self, "❌ Error", f"📊 Excel no encontrado: {excel}")
            return
        if not os.path.isdir(images):
            QMessageBox.critical(self, "❌ Error", f"🖼️ Carpeta de imágenes no encontrada: {images}")
            return
        os.makedirs(output, exist_ok=True)

        self.btn_run.setEnabled(False)
        self.btn_run.setText("🔄 Procesando...")
        self.proc_list.clear()
        self.results_list.clear()  # Limpiar la nueva lista de resultados
        self.folder_images_text.clear()
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

        self.progress_label.setText("🚀 Iniciando organización...")
        self.progress_bar.setVisible(True)
        self.tabs.setCurrentIndex(1)  # Procesando

    def update_progress(self, msg):
        self.progress_label.setText(f"⚡ {msg}")
        self.proc_list.addItem(f"📝 {msg}")
        self.proc_list.scrollToBottom()

    def update_current_img(self, img):
        self.current_img_label.setText(f"🔍 Procesando: {img}")

    def update_stats(self, stats):
        self.current_folder_stats = stats
        self.results_list.clear()

        total = sum(stats.values())

        # Agregar estadísticas generales como primer elemento
        summary_item = f"📈 TOTAL: {total} imágenes procesadas"
        self.results_list.addItem(summary_item)

        # Agregar cada carpeta como elemento clickeable
        for folder, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            folder_item = f"📁 {folder} → {count} imágenes ({percentage:.1f}%)"
            self.results_list.addItem(folder_item)

        # Limpiar el área de imágenes
        self.folder_images_text.clear()
        self.folder_images_text.setPlainText("💡 Haz clic en cualquier carpeta de la lista superior para ver las imágenes que contiene.\n\nCada carpeta muestra su nombre y el número de imágenes organizadas en ella.")

    def show_folder_images(self, item):
        """Muestra las imágenes de la carpeta seleccionada"""
        folder_name = item.text()

        # Si es el elemento de resumen total, no hacer nada
        if folder_name.startswith("📈 TOTAL"):
            self.folder_images_text.setPlainText("📊 Este es el resumen total.\n\nSelecciona una carpeta específica de la lista para ver las imágenes individuales que contiene.")
            return

        # Extraer el nombre de la carpeta del texto del elemento
        if "📁" in folder_name and "→" in folder_name:
            folder = folder_name.split("📁")[1].split("→")[0].strip()

            # Buscar las imágenes que fueron movidas a esta carpeta
            folder_images = []
            for moved_item in self.moved_list:
                item_folder = moved_item.get('folder', '')
                item_dest = moved_item.get('dest', '')
                if item_dest:
                    dest_folder = item_dest.split(os.sep)[-2] if os.sep in item_dest else item_dest
                else:
                    dest_folder = item_folder

                if dest_folder == folder:
                    img_name = moved_item.get('img', 'N/A')
                    folder_images.append(img_name)

            # Mostrar las imágenes
            if folder_images:
                images_text = f"📁 <b>{folder}</b> - {len(folder_images)} imágenes:\n\n"
                for i, img in enumerate(sorted(folder_images), 1):
                    images_text += f"{i:3d}. {img}\n"
                self.folder_images_text.setHtml(images_text)
            else:
                self.folder_images_text.setPlainText(f"No se encontraron imágenes para la carpeta '{folder}'")
        else:
            self.folder_images_text.setPlainText("Error: No se pudo identificar la carpeta seleccionada.")

    def on_finish(self, moved, pending, errors):
        self.moved_list = moved
        self.pending_data = pending
        self.errors = errors

        # Final stats
        folder_counts = Counter([d.get('folder', d.get('dest', '').split(os.sep)[-2] if d.get('dest') else '') for d in moved])
        self.update_stats(folder_counts)

        success_count = len(moved)
        pending_count = len(pending)
        error_count = len(errors)

        status_text = f"✅ ¡COMPLETADO! | 📦 Movidas: {success_count} | ⏳ Pendientes: {pending_count}"
        if error_count > 0:
            status_text += f" | ❌ Errores: {error_count}"

        self.progress_label.setText(status_text)
        self.progress_bar.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_run.setText("🚀 ¡INICIAR ORGANIZACIÓN!")
        self.tabs.setCurrentIndex(2)  # Resultados

        # Agregar pendientes a la lista
        for p in self.pending_data:
            options_text = ', '.join(p.get('options', [])[:3])
            self.pending_list.addItem(f"📄 {p['img']} → {options_text}")

        # Mostrar errores si los hay
        if errors:
            self.proc_list.addItems([f"❌ ERROR: {e}" for e in errors[-10:]])

    def start_rename(self):
        """Renombra carpetas e imágenes basándose en la base de datos"""
        output_dir = self.rename_output_path.text().strip('"')

        if not os.path.exists(output_dir):
            QMessageBox.warning(self, "⚠️ Error", f"La carpeta de salida no existe: {output_dir}")
            return

        # Confirmar acción
        reply = QMessageBox.question(self, "🔄 Confirmar Renombrado",
            "Esta acción va a:\n\n"
            "1. Renombrar carpetas según la base de datos\n"
            "2. Renombrar imágenes dentro de cada carpeta como 'NOMBRE_CARPETA # 1.jpg', etc.\n\n"
            "¿Estás seguro de continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        self.btn_rename.setEnabled(False)
        self.btn_rename.setText("🔄 Renombrando...")
        self.rename_progress_label.setText("🔄 Iniciando renombrado...")
        self.proc_list.clear()
        self.tabs.setCurrentIndex(4)  # Renombrar

        # Ejecutar renombrado
        try:
            renamed_folders, renamed_images = self.rename_folders_and_images(output_dir)
            self.rename_progress_label.setText(f"✅ ¡RENOMBRADO COMPLETADO! | 📁 Carpetas: {renamed_folders} | 🖼️ Imágenes: {renamed_images}")
            self.proc_list.addItem(f"✅ Renombrado completado: {renamed_folders} carpetas, {renamed_images} imágenes")
        except Exception as e:
            self.rename_progress_label.setText(f"❌ Error en renombrado: {str(e)}")
            self.proc_list.addItem(f"❌ Error: {str(e)}")
        finally:
            self.btn_rename.setEnabled(True)
            self.btn_rename.setText("🔄 ¡RENOMBRAR CARPETAS E IMÁGENES!")

    def rename_folders_and_images(self, output_dir):
        """Renombra carpetas e imágenes basándose en la BD"""
        # Leer nombres correctos desde BD
        db_path = os.path.join(os.path.dirname(self.excel_path.text().strip('"')), "animes.db")
        correct_names = set()

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
                                correct_names.add(title.upper())
                    except sqlite3.Error:
                        continue

                conn.close()
            except sqlite3.Error as e:
                self.proc_list.addItem(f"⚠️ Error leyendo BD: {e}. Usando nombres de carpetas existentes.")

        # Si no hay BD, usar nombres de carpetas existentes
        if not correct_names:
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    correct_names.add(item.upper())

        # Mapear nombres existentes a correctos
        renamed_folders = 0
        renamed_images = 0

        # Crear mapa de renombrado de carpetas
        folder_mapping = {}
        for existing_folder in os.listdir(output_dir):
            existing_path = os.path.join(output_dir, existing_folder)
            if not os.path.isdir(existing_path):
                continue

            # Buscar el nombre correcto más similar
            existing_upper = existing_folder.upper()
            best_match = None
            best_score = 0

            for correct_name in correct_names:
                # Calcular similitud simple
                if correct_name in existing_upper or existing_upper in correct_name:
                    score = len(set(correct_name.split()) & set(existing_upper.split()))
                    if score > best_score:
                        best_score = score
                        best_match = correct_name

            if best_match and best_match != existing_upper:
                folder_mapping[existing_folder] = best_match
            elif best_match:
                folder_mapping[existing_folder] = best_match
            else:
                # Si no hay match, usar el nombre existente en mayúscula
                folder_mapping[existing_folder] = existing_upper

        # Renombrar carpetas
        for old_name, new_name in folder_mapping.items():
            if old_name != new_name:
                old_path = os.path.join(output_dir, old_name)
                new_path = os.path.join(output_dir, new_name)

                try:
                    os.rename(old_path, new_path)
                    self.proc_list.addItem(f"📁 Renombrada carpeta: {old_name} → {new_name}")
                    renamed_folders += 1
                except OSError as e:
                    self.proc_list.addItem(f"⚠️ Error renombrando carpeta {old_name}: {e}")
                    continue

                # Usar la nueva ruta para renombrar imágenes
                folder_path = new_path
                folder_name = new_name
            else:
                folder_path = os.path.join(output_dir, old_name)
                folder_name = old_name

            # Renombrar imágenes dentro de la carpeta
            if os.path.exists(folder_path):
                images = [f for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'])]
                images.sort()  # Ordenar para consistencia

                for i, img_name in enumerate(images, 1):
                    img_path = os.path.join(folder_path, img_name)
                    _, ext = os.path.splitext(img_name)

                    new_img_name = f"{folder_name} # {i}{ext}"
                    new_img_path = os.path.join(folder_path, new_img_name)

                    try:
                        os.rename(img_path, new_img_path)
                        self.proc_list.addItem(f"🖼️ Renombrada imagen: {img_name} → {new_img_name}")
                        renamed_images += 1
                    except OSError as e:
                        self.proc_list.addItem(f"⚠️ Error renombrando imagen {img_name}: {e}")

        return renamed_folders, renamed_images

    def show_pending_detail(self, item):
        idx = self.pending_list.row(item)
        if idx < len(self.pending_data):
            p = self.pending_data[idx]
            img_name = p.get('img', 'N/A')
            options = p.get('options', [])
            confidence = p.get('confidence', 'N/A')

            detail_text = f"""
<b>📄 Archivo:</b> {img_name}
<b>🎯 Confianza:</b> {confidence}
<b>💡 Sugerencias:</b>
"""
            for i, opt in enumerate(options[:5], 1):
                detail_text += f"  {i}. {opt}\n"

            if len(options) > 5:
                detail_text += f"  ... y {len(options) - 5} más"

            self.pending_detail.setText(detail_text)
        else:
            self.pending_detail.setText("Error: No se pudo cargar la información del archivo pendiente.")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Configurar aplicación con icono y estilo moderno
    app.setApplicationName("Anime AI Organizer Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("AnimeTools")

    # Estilo global moderno
    app.setStyle("Fusion")

    # Crear y mostrar ventana
    win = App()
    win.show()

    # Mensaje de bienvenida
    QMessageBox.information(win, "🎌 ¡Bienvenido!",
        "Anime AI Organizer Pro v2.0\n\n"
        "✨ Interfaz completamente renovada\n"
        "🎨 Diseño moderno con gradientes\n"
        "🚀 Optimizado para mejor experiencia\n\n"
        "¡Disfruta organizando tus animes!")

    sys.exit(app.exec())
