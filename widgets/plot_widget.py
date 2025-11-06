from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotWidget(QWidget):
    def __init__(self, parent=None, table: QWidget | None = None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        # controls for selecting row/column and plot type
        ctrl_layout = QHBoxLayout()
        self.axis_combo = QComboBox()  # "Column" or "Row"
        self.axis_combo.addItems(["Column", "Row"])
        self.index_combo = QComboBox()  # used for row index selection or fallback
        self.x_axis_combo = QComboBox()  # select X column when plotting columns
        self.y_axis_combo = QComboBox()  # select Y column when plotting columns
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

        # matplotlib canvas
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        self.table_owner = table
        self.current_plot_type = "line"

        # connections
        self.axis_combo.currentTextChanged.connect(self._on_axis_changed)
        self.axis_combo.currentTextChanged.connect(self.update_index_options)
        self.plot_btn.clicked.connect(self.on_plot_button)
        # connect to table signals if available
        if self.table_owner is not None:
            if hasattr(self.table_owner, "structure_changed"):
                self.table_owner.structure_changed.connect(self.update_index_options)
            if hasattr(self.table_owner, "data_changed"):
                self.table_owner.data_changed.connect(self.on_auto_data_changed)
        # when selection usage toggled, refresh UI
        self.use_selection_cb.stateChanged.connect(self._on_use_selection_toggled)

        # initialize index options and visibility
        QTimer.singleShot(0, self.update_index_options)
        QTimer.singleShot(0, self._on_axis_changed)

    def _on_use_selection_toggled(self, _):
        # when using selection, index combo may be irrelevant; still update options
        self.update_index_options()

    def _on_axis_changed(self, text: str | None = None):
        axis = (text or self.axis_combo.currentText()).lower()
        if axis == "column":
            # show X/Y combos, hide index combo
            self.index_combo.hide()
            self.x_axis_combo.show()
            self.y_axis_combo.show()
        else:
            self.index_combo.show()
            self.x_axis_combo.hide()
            self.y_axis_combo.hide()

    def on_auto_data_changed(self):
        # do not auto-plot by default, but update options
        self.update_index_options()

    def on_plot_button(self):
        self.plot(self.current_plot_type)

    def update_index_options(self):
        # populate index (for rows) and X/Y combos (for columns) from current table
        self.index_combo.clear()
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        table_widget = self._get_table_widget()
        if table_widget is None:
            return

        # if using selection, keep a simple selection summary in index combo
        if self.use_selection_cb.isChecked():
            ranges = table_widget.selectedRanges()
            if ranges:
                r = ranges[0]
                summary = f"Selection r{r.topRow()}-r{r.bottomRow()} c{r.leftColumn()}-c{r.rightColumn()}"
                self.index_combo.addItem(summary)
            else:
                self.index_combo.addItem("No selection")

            # still populate X/Y comboboxes from full headers so user can choose if desired
        # populate X/Y combos with headers (or column indices if no header text)
        headers = []
        for c in range(table_widget.columnCount()):
            header_item = table_widget.horizontalHeaderItem(c)
            if header_item and header_item.text().strip() != "":
                headers.append(header_item.text())
            else:
                headers.append(str(c))
        if not headers:
            headers = [str(i) for i in range(table_widget.columnCount())]
        self.x_axis_combo.addItems(headers)
        self.y_axis_combo.addItems(headers)

        # populate index combo with row labels for row-axis mode
        labels = []
        for r in range(table_widget.rowCount()):
            first = table_widget.item(r, 0)
            labels.append(first.text() if first and first.text().strip() != "" else str(r))
        if labels:
            self.index_combo.addItems(labels)
        else:
            self.index_combo.addItems([str(i) for i in range(table_widget.rowCount())])

        # adjust visibility based on axis
        self._on_axis_changed()

    def _get_table_widget(self):
        if self.table_owner is not None:
            tw = getattr(self.table_owner, "table", None)
            if isinstance(tw, QTableWidget):
                return tw
        # fallback: search children
        for child in self.findChildren(QTableWidget):
            return child
        return None

    def plot(self, plot_type: str, axis: str | None = None, index: int | None = None):
        # if axis/index not provided, use controls
        table_widget = self._get_table_widget()
        axis = (axis or self.axis_combo.currentText().lower())
        try:
            idx = int(index) if index is not None else self.index_combo.currentIndex()
        except Exception:
            idx = 0

        self.current_plot_type = plot_type

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if table_widget is None:
            ax.text(0.5, 0.5, "No table data available", ha='center', va='center')
            self.canvas.draw()
            return

        # If using selection and selection exists, keep existing selection-based behavior
        if self.use_selection_cb.isChecked():
            ranges = table_widget.selectedRanges()
            if not ranges:
                ax.text(0.5, 0.5, "No selection made", ha='center', va='center')
                self.canvas.draw()
                return
            # reuse existing selection handling from prior implementation (unchanged)
            sel = ranges[0]
            top, bottom, left, right = sel.topRow(), sel.bottomRow(), sel.leftColumn(), sel.rightColumn()

            # Single column selection -> same as column plotting for that column over selected rows
            if left == right and top <= bottom:
                col = left
                y_values = []
                x_labels = []
                for r in range(top, bottom + 1):
                    item = table_widget.item(r, col)
                    if item is None:
                        continue
                    text_val = item.text().strip()
                    if text_val == "":
                        continue
                    try:
                        y = float(text_val)
                    except Exception:
                        continue
                    y_values.append(y)
                    first = table_widget.item(r, 0)
                    label = first.text().strip() if (first is not None and first.text().strip() != "") else str(r)
                    x_labels.append(label)
                if len(y_values) == 0:
                    ax.text(0.5, 0.5, "No numeric data in selection", ha='center', va='center')
                    self.canvas.draw()
                    return
                x_positions = list(range(len(y_values)))
                if plot_type == "line":
                    ax.plot(x_positions, y_values, marker='-', label=table_widget.horizontalHeaderItem(col).text() if table_widget.horizontalHeaderItem(col) else f"Col {col}")
                elif plot_type == "scatter":
                    ax.scatter(x_positions, y_values, c='tab:blue')
                elif plot_type == "bar":
                    ax.bar(x_positions, y_values, color='tab:green')
                ax.set_xticks(x_positions)
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
                ax.set_xlabel("Row")
                ax.set_ylabel(table_widget.horizontalHeaderItem(col).text() if table_widget.horizontalHeaderItem(col) else f"Col {col}")
                ax.set_title(f"{plot_type.capitalize()} of column {col} (selection)")
                ax.legend()
                self.figure.tight_layout()
                self.canvas.draw()
                return

            # Single row selection -> same as row plotting for that row across selected columns
            if top == bottom and left <= right:
                row = top
                headers = []
                values = []
                for c in range(left, right + 1):
                    header_item = table_widget.horizontalHeaderItem(c)
                    headers.append(header_item.text() if header_item else str(c))
                    item = table_widget.item(row, c)
                    if item is None:
                        values.append(None)
                        continue
                    text_val = item.text().strip()
                    if text_val == "":
                        values.append(None)
                        continue
                    try:
                        y = float(text_val)
                    except Exception:
                        values.append(None)
                        continue
                    values.append(y)
                x_positions = []
                y_filtered = []
                x_labels = []
                for i, v in enumerate(values):
                    if v is None:
                        continue
                    x_positions.append(len(x_positions))
                    y_filtered.append(v)
                    x_labels.append(headers[i])
                if len(y_filtered) == 0:
                    ax.text(0.5, 0.5, "No numeric data in selection", ha='center', va='center')
                    self.canvas.draw()
                    return
                if plot_type == "line":
                    ax.plot(x_positions, y_filtered, marker='o')
                elif plot_type == "scatter":
                    ax.scatter(x_positions, y_filtered, c='tab:blue')
                elif plot_type == "bar":
                    ax.bar(x_positions, y_filtered, color='tab:green')
                ax.set_xticks(x_positions)
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
                ax.set_xlabel("Column")
                ax.set_ylabel(f"Row {row} values")
                ax.set_title(f"{plot_type.capitalize()} of row {row} (selection)")
                self.figure.tight_layout()
                self.canvas.draw()
                return

            # Rectangular selection with multiple cols and rows: keep previous behavior (plot columns across rows)
            col_count = right - left + 1
            row_count = bottom - top + 1
            x_labels = []
            series_list = []
            series_labels = []
            for r in range(top, bottom + 1):
                first = table_widget.item(r, 0)
                label = first.text().strip() if (first is not None and first.text().strip() != "") else str(r)
                x_labels.append(label)
            for c in range(left, right + 1):
                vals = []
                for r in range(top, bottom + 1):
                    item = table_widget.item(r, c)
                    if item is None:
                        vals.append(None)
                        continue
                    text_val = item.text().strip()
                    try:
                        v = float(text_val)
                    except Exception:
                        v = None
                    vals.append(v)
                y_filtered = []
                x_filtered = []
                for i, v in enumerate(vals):
                    if v is None:
                        continue
                    y_filtered.append(v)
                    x_filtered.append(i)
                if len(y_filtered) == 0:
                    continue
                series_list.append((y_filtered, x_filtered))
                header_item = table_widget.horizontalHeaderItem(c)
                series_labels.append(header_item.text() if header_item and header_item.text().strip() != "" else f"Col {c}")
            if not series_list:
                ax.text(0.5, 0.5, "No numeric data in selection", ha='center', va='center')
                self.canvas.draw()
                return
            if plot_type == "line":
                for (yvals, xpos), lbl in zip(series_list, series_labels):
                    ax.plot(xpos, yvals, marker='o', label=lbl)
            elif plot_type == "scatter":
                for (yvals, xpos), lbl in zip(series_list, series_labels):
                    ax.scatter(xpos, yvals, label=lbl)
            elif plot_type == "bar":
                n = len(series_list)
                m = max(len(xp) for (_, xp) in series_list)
                base_positions = list(range(m))
                bar_width = 0.8 / max(1, n)
                for j, ((yvals, xpos), lbl) in enumerate(zip(series_list, series_labels)):
                    offsets = [pos - 0.4 + j * bar_width + bar_width / 2 for pos in xpos]
                    ax.bar(offsets, yvals, width=bar_width, label=lbl)
            unique_positions = sorted({p for (_, xp) in series_list for p in xp})
            ax.set_xticks(list(range(len(unique_positions))))
            mapped_labels = [x_labels[p] if 0 <= p < len(x_labels) else str(p) for p in unique_positions]
            ax.set_xticklabels(mapped_labels, rotation=45, ha='right')
            ax.set_xlabel("Row (selection)")
            ax.set_ylabel("Value")
            ax.set_title(f"{plot_type.capitalize()} of selection")
            ax.legend()
            self.figure.tight_layout()
            self.canvas.draw()
            return

        # fallback: no selection usage -> use new X/Y column selection when axis == "column"
        x_labels = []
        y_values = []

        if axis == "column":
            # use X and Y combo selections
            x_col = self.x_axis_combo.currentIndex()
            y_col = self.y_axis_combo.currentIndex()
            if y_col < 0 or y_col >= table_widget.columnCount():
                ax.text(0.5, 0.5, "Invalid Y column", ha='center', va='center')
                self.canvas.draw()
                return
            if x_col < 0 or x_col >= table_widget.columnCount():
                ax.text(0.5, 0.5, "Invalid X column", ha='center', va='center')
                self.canvas.draw()
                return

            x_vals = []
            y_vals = []
            x_labels_text = []
            for r in range(table_widget.rowCount()):
                item_x = table_widget.item(r, x_col)
                item_y = table_widget.item(r, y_col)
                if item_y is None:
                    continue
                text_y = item_y.text().strip()
                if text_y == "":
                    continue
                try:
                    y = float(text_y)
                except Exception:
                    continue
                # accept x even if non-numeric (we will use positions)
                x_text = item_x.text().strip() if item_x is not None else str(r)
                # try numeric x
                try:
                    xnum = float(x_text)
                except Exception:
                    xnum = None
                x_vals.append(xnum if xnum is not None else x_text)
                y_vals.append(y)
                x_labels_text.append(x_text)

            if len(y_vals) == 0:
                ax.text(0.5, 0.5, "No numeric Y data in selected column", ha='center', va='center')
                self.canvas.draw()
                return

            # if X values are numeric for all rows, plot directly; else use indices and set xticklabels
            if all(isinstance(xv, (int, float)) for xv in x_vals):
                xs = [float(xv) for xv in x_vals]
                if plot_type == "line":
                    ax.plot(xs, y_vals, marker='o')
                elif plot_type == "scatter":
                    ax.scatter(xs, y_vals)
                elif plot_type == "bar":
                    ax.bar(xs, y_vals)
                ax.set_xlabel(table_widget.horizontalHeaderItem(x_col).text() if table_widget.horizontalHeaderItem(x_col) else f"Col {x_col}")
            else:
                xs = list(range(len(y_vals)))
                if plot_type == "line":
                    ax.plot(xs, y_vals, marker='o')
                elif plot_type == "scatter":
                    ax.scatter(xs, y_vals)
                elif plot_type == "bar":
                    ax.bar(xs, y_vals)
                ax.set_xticks(xs)
                ax.set_xticklabels(x_labels_text, rotation=45, ha='right')
                ax.set_xlabel(table_widget.horizontalHeaderItem(x_col).text() if table_widget.horizontalHeaderItem(x_col) else f"Col {x_col}")

            ax.set_ylabel(table_widget.horizontalHeaderItem(y_col).text() if table_widget.horizontalHeaderItem(y_col) else f"Col {y_col}")
            ax.set_title(f"{plot_type.capitalize()} of {ax.get_ylabel()} vs {ax.get_xlabel()}")

        else:  # row plotting across columns (unchanged)
            row = idx
            if row < 0 or row >= table_widget.rowCount():
                ax.text(0.5, 0.5, "Invalid row", ha='center', va='center')
                self.canvas.draw()
                return
            headers = []
            values = []
            for c in range(table_widget.columnCount()):
                header_item = table_widget.horizontalHeaderItem(c)
                headers.append(header_item.text() if header_item else str(c))
                item = table_widget.item(row, c)
                if item is None:
                    values.append(None)
                    continue
                text_val = item.text().strip()
                if text_val == "":
                    values.append(None)
                    continue
                try:
                    y = float(text_val)
                except Exception:
                    values.append(None)
                    continue
                values.append(y)
            x_positions = []
            y_filtered = []
            x_labels = []
            for i, v in enumerate(values):
                if v is None:
                    continue
                x_positions.append(len(x_positions))
                y_filtered.append(v)
                x_labels.append(headers[i])
            if len(y_filtered) == 0:
                ax.text(0.5, 0.5, "No numeric data in selected row", ha='center', va='center')
                self.canvas.draw()
                return
            if plot_type == "line":
                ax.plot(x_positions, y_filtered, marker='o')
            elif plot_type == "scatter":
                ax.scatter(x_positions, y_filtered, c='tab:blue')
            elif plot_type == "bar":
                ax.bar(x_positions, y_filtered, color='tab:green')
            ax.set_xticks(x_positions)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            ax.set_xlabel("Column")
            ax.set_ylabel(f"Row {row} values")
            ax.set_title(f"{plot_type.capitalize()} of row {row}")

        self.figure.tight_layout()
        self.canvas.draw()
