from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import * 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtPlot")

        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        view_menu = menu.addMenu("&View")
        plot_menu = menu.addMenu("&Plot")
        analysis_menu = menu.addMenu("&Analysis")
        statistics_menu = menu.addMenu("&Statistics")
        table_menu = menu.addMenu("&Table")
        windows_menu = menu.addMenu("&Windows")
        help_menu = menu.addMenu("&Help")

app = QApplication([])
window = MainWindow()
window.show()
app.exec()