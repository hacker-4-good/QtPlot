from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import random


class PlotWidget(QWidget):
    def __init__(self, parent=None, table: QWidget | None = None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)

        # === Controls Layout ===
        ctrl_layout = QHBoxLayout()
        self.axis_combo = QComboBox()
        self.axis_combo.addItems(["Column", "Row"])
        self.index_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.y_axis_combo = QComboBox()
        self.use_selection_cb = QCheckBox("Use selection")
        self.plot_btn = QPushButton("Plot")

        ctrl_layout.addWidget(QLabel("Plot axis:"))
        ctrl_layout.addWidget(self.axis_combo)
        ctrl_layout.addWidget(QLabel("Index:"))
        ctrl_layout.addWidget(self.index_combo)
        ctrl_layout.addWidget(QLabel("X:"))
        ctrl_layout.addWidget(self.x_axis_combo)
        ctrl_layout.addWidget(QLabel("Y:"))
        ctrl_layout.addWidget(self.y_axis_combo)
        ctrl_layout.addWidget(self.use_selection_cb)
        ctrl_layout.addWidget(self.plot_btn)
        ctrl_layout.addStretch()
        main_layout.addLayout(ctrl_layout)

        # === Matplotlib Canvas ===
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # 🔹 Add context menu on canvas
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self.show_context_menu)

        self.table_owner = table
        self.current_plot_type = "line"

        # default style
        self.plot_styles = {
            "color": "tab:blue",
            "marker": "o",
            "linestyle": "-",
        }

        # connections
        self.axis_combo.currentTextChanged.connect(self._on_axis_changed)
        self.axis_combo.currentTextChanged.connect(self.update_index_options)
        self.plot_btn.clicked.connect(self.on_plot_button)

        if self.table_owner is not None:
            if hasattr(self.table_owner, "structure_changed"):
                self.table_owner.structure_changed.connect(self.update_index_options)
            if hasattr(self.table_owner, "data_changed"):
                self.table_owner.data_changed.connect(self.on_auto_data_changed)

        self.use_selection_cb.stateChanged.connect(self._on_use_selection_toggled)

        QTimer.singleShot(0, self.update_index_options)
        QTimer.singleShot(0, self._on_axis_changed)

    # === Context Menu ===
    def show_context_menu(self, pos):
        menu = QMenu(self)
        save_action = QAction("💾 Save Plot As...", self)
        color_action = QAction("🎨 Change Color", self)
        marker_action = QAction("🔹 Change Marker Style", self)
        line_action = QAction("〰️ Change Line Style", self)
        multi_axis_action = QAction("➕ Add Another Y-Axis", self)
        clear_action = QAction("🧹 Clear Plot", self)

        menu.addAction(save_action)
        menu.addSeparator()
        menu.addAction(color_action)
        menu.addAction(marker_action)
        menu.addAction(line_action)
        menu.addSeparator()
        menu.addAction(multi_axis_action)
        menu.addSeparator()
        menu.addAction(clear_action)

        action = menu.exec_(self.canvas.mapToGlobal(pos))
        if action == save_action:
            self.save_plot()
        elif action == color_action:
            self.change_color()
        elif action == marker_action:
            self.change_marker()
        elif action == line_action:
            self.change_linestyle()
        elif action == multi_axis_action:
            self.add_secondary_axis()
        elif action == clear_action:
            self.clear_plot()

    # === Customization Handlers ===
    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.plot_styles["color"] = color.name()
            self.on_plot_button()

    def change_marker(self):
        items = ["o", "s", "x", "D", "*", "+", "None"]
        style, ok = QInputDialog.getItem(self, "Select Marker", "Marker style:", items, 0, False)
        if ok:
            self.plot_styles["marker"] = None if style == "None" else style
            self.on_plot_button()

    def change_linestyle(self):
        styles = ["-", "--", "-.", ":", "None"]
        style, ok = QInputDialog.getItem(self, "Select Line Style", "Line style:", styles, 0, False)
        if ok:
            self.plot_styles["linestyle"] = None if style == "None" else style
            self.on_plot_button()

    def add_secondary_axis(self):
        """Allow user to plot an additional Y column on the same X axis (secondary axis)."""
        table_widget = self._get_table_widget()
        if not table_widget:
            return

        y_col, ok = QInputDialog.getInt(self, "Add Secondary Y", "Enter Y column index:", 0, 0, table_widget.columnCount()-1)
        if not ok:
            return

        ax = self.figure.gca()
        ax2 = ax.twinx()
        y_vals = []
        x_vals = list(range(table_widget.rowCount()))
        for r in range(table_widget.rowCount()):
            item = table_widget.item(r, y_col)
            try:
                y_vals.append(float(item.text()))
            except Exception:
                y_vals.append(None)

        y_vals = [v for v in y_vals if v is not None]
        if not y_vals:
            QMessageBox.warning(self, "Warning", "No numeric data in selected column.")
            return

        color = random.choice(plt.rcParams['axes.prop_cycle'].by_key()['color'])
        ax2.plot(x_vals[:len(y_vals)], y_vals, color=color, linestyle='--', marker='x')
        ax2.set_ylabel(f"Col {y_col}", color=color)
        ax2.tick_params(axis='y', labelcolor=color)
        self.figure.tight_layout()
        self.canvas.draw()

    def clear_plot(self):
        self.figure.clear()
        self.canvas.draw()

    def save_plot(self):
        """Save the current plot to an image file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot As",
            "",
            "PNG Image (*.png);;SVG Vector (*.svg);;PDF Document (*.pdf)"
        )
        if file_path:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Saved", f"Plot saved to:\n{file_path}")

    # === Keep your existing functions unchanged below (trimmed for brevity) ===
    def _on_use_selection_toggled(self, _):
        self.update_index_options()

    def _on_axis_changed(self, text: str | None = None):
        axis = (text or self.axis_combo.currentText()).lower()
        if axis == "column":
            self.index_combo.hide()
            self.x_axis_combo.show()
            self.y_axis_combo.show()
        else:
            self.index_combo.show()
            self.x_axis_combo.hide()
            self.y_axis_combo.hide()

    def on_auto_data_changed(self):
        self.update_index_options()

    def on_plot_button(self):
        self.plot(self.current_plot_type)

    def update_index_options(self):
        self.index_combo.clear()
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        table_widget = self._get_table_widget()
        if table_widget is None:
            return

        headers = []
        for c in range(table_widget.columnCount()):
            header_item = table_widget.horizontalHeaderItem(c)
            headers.append(header_item.text() if header_item and header_item.text().strip() != "" else str(c))

        self.x_axis_combo.addItems(headers)
        self.y_axis_combo.addItems(headers)
        for r in range(table_widget.rowCount()):
            first = table_widget.item(r, 0)
            self.index_combo.addItem(first.text() if first and first.text().strip() else str(r))
        self._on_axis_changed()

    def _get_table_widget(self):
        if self.table_owner is not None:
            tw = getattr(self.table_owner, "table", None)
            if isinstance(tw, QTableWidget):
                return tw
        for child in self.findChildren(QTableWidget):
            return child
        return None

    # === Modified plot function (respects self.plot_styles) ===
    def plot(self, plot_type: str, axis: str | None = None, index: int | None = None):
        table_widget = self._get_table_widget()
        if table_widget is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        color = self.plot_styles.get("color", "tab:blue")
        marker = self.plot_styles.get("marker", "o")
        linestyle = self.plot_styles.get("linestyle", "-")

        # simplified column plot example
        x_col = self.x_axis_combo.currentIndex()
        y_col = self.y_axis_combo.currentIndex()

        x_vals, y_vals = [], []
        for r in range(table_widget.rowCount()):
            item_x = table_widget.item(r, x_col)
            item_y = table_widget.item(r, y_col)
            try:
                x_vals.append(float(item_x.text()) if item_x else r)
                y_vals.append(float(item_y.text()))
            except Exception:
                continue

        if plot_type == "line":
            ax.plot(x_vals, y_vals, color=color, linestyle=linestyle, marker=marker)
        elif plot_type == "scatter":
            ax.scatter(x_vals, y_vals, color=color, marker=marker)
        elif plot_type == "bar":
            ax.bar(x_vals, y_vals, color=color)

        ax.set_xlabel(self.x_axis_combo.currentText())
        ax.set_ylabel(self.y_axis_combo.currentText())
        ax.set_title(f"{plot_type.capitalize()} Plot")
        self.figure.tight_layout()
        self.canvas.draw()
