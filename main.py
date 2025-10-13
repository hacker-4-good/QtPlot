from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from widgets.table_editor import TableEditor 
from widgets.plot_widget import PlotWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtPlot")

        menu = self.menuBar()
        menu.addMenu("&File")
        menu.addMenu("&Edit")
        menu.addMenu("&View")
        plot_menu = menu.addMenu("&Plot")
        menu.addMenu("&Analysis")
        menu.addMenu("&Statistics")
        menu.addMenu("&Table")
        menu.addMenu("&Windows")
        menu.addMenu("&Help")

        # Plot actions
        line_action = QAction("Line plot", self)
        scatter_action = QAction("Scatter plot", self)
        bar_action = QAction("Bar plot", self)
        plot_menu.addAction(line_action)
        plot_menu.addAction(scatter_action)
        plot_menu.addAction(bar_action)

        line_action.triggered.connect(lambda: self.show_plot("line"))
        scatter_action.triggered.connect(lambda: self.show_plot("scatter"))
        bar_action.triggered.connect(lambda: self.show_plot("bar"))

        # Add the TableEditor as the central widget (single-page)
        self.table_editor = TableEditor()
        self.setCentralWidget(self.table_editor)

        # single dock for plots (reuse)
        self.plot_dock: QDockWidget | None = None

    def show_plot(self, plot_type: str):
        title = f"Plot - {plot_type.capitalize()}"
        if self.plot_dock is None:
            self.plot_dock = QDockWidget(title, self)
            self.plot_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            plot_widget = PlotWidget(self, table=self.table_editor)
            self.plot_dock.setWidget(plot_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, self.plot_dock)
        else:
            self.plot_dock.setWindowTitle(title)
            plot_widget = self.plot_dock.widget()
            if plot_widget is None or not isinstance(plot_widget, PlotWidget):
                plot_widget = PlotWidget(self, table=self.table_editor)
                self.plot_dock.setWidget(plot_widget)
            else:
                plot_widget.table_owner = self.table_editor
        # set desired plot type and update selectors
        plot_widget.current_plot_type = plot_type
        plot_widget.update_index_options()
        # initial plot attempt
        plot_widget.plot(plot_type)
        self.plot_dock.show()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    app.exec()