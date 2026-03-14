if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en gui_app.py:\n{e}\n\n{traceback.format_exc()}")
import sys
from PySide6.QtWidgets import *

from organizer_core import organize_images


class App(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Anime AI Organizer")

        self.setGeometry(200, 200, 600, 300)

        layout = QVBoxLayout()

        self.excel = QLineEdit()
        self.images = QLineEdit()
        self.output = QLineEdit()

        btn_excel = QPushButton("Seleccionar Excel")
        btn_img = QPushButton("Seleccionar Imágenes")
        btn_out = QPushButton("Seleccionar Salida")

        btn_run = QPushButton("Organizar")

        btn_excel.clicked.connect(self.pick_excel)
        btn_img.clicked.connect(self.pick_images)
        btn_out.clicked.connect(self.pick_output)
        btn_run.clicked.connect(self.run)

        layout.addWidget(self.excel)
        layout.addWidget(btn_excel)

        layout.addWidget(self.images)
        layout.addWidget(btn_img)

        layout.addWidget(self.output)
        layout.addWidget(btn_out)

        layout.addWidget(btn_run)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def pick_excel(self):

        f = QFileDialog.getOpenFileName(self)[0]

        self.excel.setText(f)

    def pick_images(self):

        f = QFileDialog.getExistingDirectory(self)

        self.images.setText(f)

    def pick_output(self):

        f = QFileDialog.getExistingDirectory(self)

        self.output.setText(f)

    def run(self):

        organize_images(
            self.excel.text(),
            self.images.text(),
            self.output.text()
        )


app = QApplication(sys.argv)

window = App()

window.show()

sys.exit(app.exec())