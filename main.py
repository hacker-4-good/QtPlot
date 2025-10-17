from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from widgets.table_editor import TableEditor 
from widgets.plot_widget import PlotWidget
from widgets.chat_widget import ChatWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtPlot")

        menu = self.menuBar()
        # keep file menu reference to add Open CSV
        file_menu = menu.addMenu("&File")
        menu.addMenu("&Edit")
        menu.addMenu("&View")
        plot_menu = menu.addMenu("&Plot")
        menu.addMenu("&Analysis")
        menu.addMenu("&Statistics")
        menu.addMenu("&Table")
        menu.addMenu("&Windows")
        menu.addMenu("&Help")

        # File -> Open CSV action
        open_csv_action = QAction("Open CSV...", self)
        file_menu.addAction(open_csv_action)
        open_csv_action.triggered.connect(self.open_csv_file)

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

        # Chatbot menu under Analysis
        analysis_menu = menu.addMenu("&Chat")
        open_chat_action = QAction("Open Chatbot", self)
        analysis_menu.addAction(open_chat_action)
        open_chat_action.triggered.connect(self.show_chatbot)

        # Add the TableEditor as the central widget (single-page)
        self.table_editor = TableEditor()
        self.setCentralWidget(self.table_editor)

        # single dock for plots (reuse)
        self.plot_dock: QDockWidget | None = None
        # single dock for chatbot (reuse)
        self.chat_dock: QDockWidget | None = None

        # keep a reference to the last created plot widget so chat can attach to it
        self.last_plot_widget: PlotWidget | None = None

    def open_csv_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        # ask whether first row is header
        resp = QMessageBox.question(self, "CSV header", "Does the CSV include a header row?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        has_header = resp == QMessageBox.StandardButton.Yes
        self.table_editor.load_csv(path, has_header=has_header)

    def show_plot(self, plot_type: str):
        title = f"Plot - {plot_type.capitalize()}"
        if self.plot_dock is None:
            self.plot_dock = QDockWidget(title, self)
            self.plot_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            plot_widget = PlotWidget(self, table=self.table_editor)
            self.plot_dock.setWidget(plot_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, self.plot_dock)
            self.last_plot_widget = plot_widget
        else:
            self.plot_dock.setWindowTitle(title)
            plot_widget = self.plot_dock.widget()
            if plot_widget is None or not isinstance(plot_widget, PlotWidget):
                plot_widget = PlotWidget(self, table=self.table_editor)
                self.plot_dock.setWidget(plot_widget)
            else:
                plot_widget.table_owner = self.table_editor
            self.last_plot_widget = plot_widget
        # set desired plot type and update selectors
        plot_widget.current_plot_type = plot_type
        plot_widget.update_index_options()
        # initial plot attempt
        plot_widget.plot(plot_type)
        self.plot_dock.show()

    def show_chatbot(self):
        title = "Chatbot"
        if self.chat_dock is None:
            self.chat_dock = QDockWidget(title, self)
            self.chat_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            # attach current plot if exists (otherwise chat can still use table)
            chat_widget = ChatWidget(self, table_editor=self.table_editor, plot_widget=self.last_plot_widget)
            self.chat_dock.setWidget(chat_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, self.chat_dock)
        else:
            self.chat_dock.setWindowTitle(title)
            chat_widget = self.chat_dock.widget()
            if chat_widget is None or not isinstance(chat_widget, ChatWidget):
                chat_widget = ChatWidget(self, table_editor=self.table_editor, plot_widget=self.last_plot_widget)
                self.chat_dock.setWidget(chat_widget)
            else:
                # update references to latest table/plot
                chat_widget.table_editor = self.table_editor
                chat_widget.plot_widget = self.last_plot_widget
        self.chat_dock.show()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    app.exec()