from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from widgets.table_editor import TableEditor 
from widgets.plot_widget import PlotWidget
from widgets.chat_widget import ChatWidget
import os, sys 

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class AddFunctionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QtiPlot - Add function curve")
        self.setFixedSize(420, 450)
        main_layout = QVBoxLayout(self)

        # --- Curve Type ---
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Curve Type"))
        self.curve_type = QComboBox()
        self.curve_type.addItems(["Function", "Parametric Plot", "Polar Plot"])
        row1.addWidget(self.curve_type)
        main_layout.addLayout(row1)

        # --- Comment --- 
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Comment"))
        self.commit_edit = QLineEdit()
        row2.addWidget(self.commit_edit)
        main_layout.addLayout(row2)

        # --- f(x) editor --- 
        main_layout.addWidget(QLabel("f(x) ="))
        self.function_edit = QTextEdit()
        main_layout.addWidget(self.function_edit)

        # --- From/To ---
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("From x="))
        self.from_spin = QDoubleSpinBox()
        self.from_spin.setValue(0)
        row3.addWidget(self.from_spin)

        row3.addWidget(QLabel("To x="))
        self.to_spin = QDoubleSpinBox()
        self.to_spin.setValue(1)
        row3.addWidget(self.to_spin)
        main_layout.addLayout(row3)

        # --- Points ---
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Points"))
        self.point_spin = QSpinBox()
        self.point_spin.setRange(2, 100000)
        self.point_spin.setValue(100)
        row4.addWidget(self.point_spin)
        main_layout.addLayout(row4)

        # --- Button --- 
        btn_row = QHBoxLayout()
        self.help_btn = QPushButton("Help")
        self.add_btn = QPushButton("Add Function")
        self.ok_btn = QPushButton("Ok")
        self.close_btn = QPushButton("Close")

        self.close_btn.clicked.connect(self.close)

        btn_row.addWidget(self.help_btn)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.close_btn)

        main_layout.addLayout(btn_row)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtPlot")
        self.resize(1200, 800)

        # Workspace area 
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.create_default_table()

        self.mdi.subWindowActivated.connect(self.on_subwindow_activated)

        menu = self.menuBar()
        # keep file menu reference to add Open CSV
        file_menu = menu.addMenu("&File")
        menu.addMenu("&Edit")
        menu.addMenu("&View")
        plot_menu = menu.addMenu("&Plot")
        menu.addMenu("&Analysis")
        menu.addMenu("&Statistics")
        table_menu = menu.addMenu("&Table")
        menu.addMenu("&Windows")
        menu.addMenu("&Help")

        # File -> Open CSV action, New Table
        open_csv_action = QAction("Open CSV...", self)
        file_menu.addAction(open_csv_action)
        open_csv_action.triggered.connect(self.open_csv_file)
        new_table_action = QAction("New Table", self)
        file_menu.addAction(new_table_action)
        new_table_action.triggered.connect(self.new_table)
        file_menu.addSeparator()

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


        # Table Menu
        rename_table_action = QAction("Rename Table", self)
        table_menu.addAction(rename_table_action)
        rename_table_action.triggered.connect(self.rename_active_table)
        
        # single dock for plots (reuse)
        self.plot_dock: QDockWidget | None = None
        # single dock for chatbot (reuse)
        self.chat_dock: QDockWidget | None = None

        # keep a reference to the last created plot widget so chat can attach to it
        self.last_plot_widget: PlotWidget | None = None

        self.create_toolbar()

    def on_subwindow_activated(self, sub):
        if sub and isinstance(sub.widget(), TableEditor):
            self.table_editor = sub.widget()

    def new_table(self):
        table = TableEditor()
        sub = QMdiSubWindow()
        sub.setWidget(table)
        sub.setWindowTitle(f"Table{len(self.mdi.subWindowList())+1}")
        sub.resize(600, 400)
        self.mdi.addSubWindow(sub)
        sub.show()
        self.mdi.setActiveSubWindow(sub)
        self.table_editor = table 

    def rename_active_table(self):
        sub= self.mdi.activeSubWindow()
        if not sub or not isinstance(sub.widget(), TableEditor):
            QMessageBox.information(self, "Rename Table", "No table is active")
            return 
        old_name = sub.windowTitle()
        new_name, ok = QInputDialog.getText(self, "Rename Table", "New table name:", text=old_name)
        if ok and new_name.strip():
            sub.setWindowTitle(new_name.strip())

    def create_default_table(self):
        table = TableEditor()
        sub = QMdiSubWindow()
        sub.setWidget(table)
        sub.setWindowTitle("Table1")
        sub.resize(400, 300)
        self.mdi.addSubWindow(sub)
        sub.show()
        self.table_editor = table
    
    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.addToolBar(Qt.TopToolBarArea, toolbar)

        file_icon = QAction(QIcon(resource_path("images/file_icon.png")), "", self)
        file_icon.setToolTip("Open a new project")
        toolbar.addAction(file_icon)
        file_icon.triggered.connect(self.open_file_window)

        new_function_icon = QAction(QIcon(resource_path("images/function_icon.png")), "", self)
        new_function_icon.setToolTip("Create a new 2D function plot")
        toolbar.addAction(new_function_icon)
        new_function_icon.triggered.connect(self.open_add_function_dialog)

        new_project_icon = QAction(QIcon(resource_path("images/project_icon.png")), "", self)
        new_project_icon.setToolTip("Open project")
        toolbar.addAction(new_project_icon)

        save_project_icon = QAction(QIcon(resource_path("images/save_project_icon.png")), "", self)
        save_project_icon.setToolTip("Save Project")
        toolbar.addAction(save_project_icon)

        save_project_as_icon = QAction(QIcon(resource_path("images/save_project_as_icon.png")), "", self)
        save_project_as_icon.setToolTip("Save Project As")
        toolbar.addAction(save_project_as_icon)

        import_data_icon = QAction(QIcon(resource_path("images/import_data_icon.png")), "", self)
        import_data_icon.setToolTip("Import Data File(s)")
        toolbar.addAction(import_data_icon)

        duplicate_window_icon = QAction(QIcon(resource_path("images/duplicate_window_icon.png")), "", self)
        duplicate_window_icon.setToolTip("Duplicate Window")
        toolbar.addAction(duplicate_window_icon)

        print_window_icon = QAction(QIcon(resource_path("images/print_window_icon.png")), "", self)
        print_window_icon.setToolTip("Print Window")
        toolbar.addAction(print_window_icon)

        print_preview_icon = QAction(QIcon(resource_path("images/print_preview_icon.png")), "", self)
        print_preview_icon.setToolTip("Print Preview")
        toolbar.addAction(print_preview_icon)

        export_pdf_icon = QAction(QIcon(resource_path("images/export_pdf_icon.png")), "", self)
        export_pdf_icon.setToolTip("Export to PDF")
        toolbar.addAction(export_pdf_icon)

        project_explorer_icon = QAction(QIcon(resource_path("images/project_explorer_icon.png")), "", self)
        project_explorer_icon.setToolTip("Show Project Explorer")
        toolbar.addAction(project_explorer_icon)

        analysis_result_icon = QAction(QIcon(resource_path("images/analysis_result_icon.png")), "", self)
        analysis_result_icon.setToolTip("Show Analysis Result")
        toolbar.addAction(analysis_result_icon)

        serial_monitor_icon = QAction(QIcon(resource_path("images/serial_monitor_icon.png")), "", self)
        serial_monitor_icon.setToolTip("Serial Monitor")
        toolbar.addAction(serial_monitor_icon)

        undo_icon = QAction(QIcon(resource_path("images/undo_icon.png")), "", self)
        undo_icon.setToolTip("Undo Changes")
        toolbar.addAction(undo_icon)

        redo_icon = QAction(QIcon(resource_path("images/redo_icon.png")), "", self)
        redo_icon.setToolTip("Redo Changes")
        toolbar.addAction(redo_icon)

        cut_selection_icon = QAction(QIcon(resource_path("images/cut_selection_icon.png")), "", self)
        cut_selection_icon.setToolTip("Cut selection")
        toolbar.addAction(cut_selection_icon)

        copy_selection_icon = QAction(QIcon(resource_path("images/copy_selection_icon.png")), "", self)
        copy_selection_icon.setToolTip("Copy selection")
        toolbar.addAction(copy_selection_icon)

        paste_selection_icon = QAction(QIcon(resource_path("images/paste_selection_icon.png")), "", self)
        paste_selection_icon.setToolTip("Paste selection")
        toolbar.addAction(paste_selection_icon)

        delete_selection_icon = QAction(QIcon(resource_path("images/delete_selection_icon.png")), "", self)
        delete_selection_icon.setToolTip("Delete selection")
        toolbar.addAction(delete_selection_icon)

        line_plot_icon = QAction(QIcon(resource_path("images/line_plot_icon.png")), "", self)
        line_plot_icon.setToolTip("Plot as Line")
        toolbar.addAction(line_plot_icon)

        symbols_plot_icon = QAction(QIcon(resource_path("images/symbols_plot_icon.png")), "", self)
        symbols_plot_icon.setToolTip("Plot as Symbols")
        toolbar.addAction(symbols_plot_icon)

        line_symbols_plot_icon = QAction(QIcon(resource_path("images/line_symbols_plot_icon.png")), "", self)
        line_symbols_plot_icon.setToolTip("Plot as Line + Symbols")
        toolbar.addAction(line_symbols_plot_icon)

        bar_plot_icon = QAction(QIcon(resource_path("images/bar_plot_icon.png")), "", self)
        bar_plot_icon.setToolTip("Plot with verticle bars")
        toolbar.addAction(bar_plot_icon)

        plot_area_icon = QAction(QIcon(resource_path("images/plot_area_icon.png")), "", self)
        plot_area_icon.setToolTip("Plot area")
        toolbar.addAction(plot_area_icon)

        box_plot_icon = QAction(QIcon(resource_path("images/box_plot_icon.png")), "", self)
        box_plot_icon.setToolTip("Box and Whisker Plot")
        toolbar.addAction(box_plot_icon)

        vectors_icon = QAction(QIcon(resource_path("images/vectors_icon.png")), "", self)
        vectors_icon.setToolTip("Vectors XYXY")
        toolbar.addAction(vectors_icon)

        double_yaxis_icon = QAction(QIcon(resource_path("images/double_yaxis_icon.png")), "", self)
        double_yaxis_icon.setToolTip("Double Y axis")
        toolbar.addAction(double_yaxis_icon)

        bars_icon = QAction(QIcon(resource_path("images/bars_icon.png")), "", self)
        bars_icon.setToolTip("Inline Bars")
        toolbar.addAction(bars_icon)

    
    def open_add_function_dialog(self):
        dialog = AddFunctionDialog(self)
        dialog.exec()

    def open_file_window(self):
        self.file_window = MainWindow()
        self.file_window.show()
        self.file_window.raise_()
        self.file_window.activateWindow()

    def open_csv_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return

        resp = QMessageBox.question(
            self,
            "CSV header",
            "Does the CSV include a header row?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        has_header = resp == QMessageBox.StandardButton.Yes

        table = TableEditor()
        sub = QMdiSubWindow()
        sub.setWidget(table)
        sub.setAttribute(Qt.WA_DeleteOnClose)
        sub.setWindowTitle(f"Table{len(self.mdi.subWindowList())+1}")
        sub.resize(700, 500)

        self.mdi.addSubWindow(sub)
        sub.show()
        self.mdi.setActiveSubWindow(sub)

        table.load_csv_in_background(path, has_header=has_header)


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