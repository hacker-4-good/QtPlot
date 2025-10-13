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
        self.index_combo = QComboBox()
        self.use_selection_cb = QCheckBox("Use selection")
        self.plot_btn = QPushButton("Plot")
        ctrl_layout.addWidget(QLabel("Plot axis:"))
        ctrl_layout.addWidget(self.axis_combo)
        ctrl_layout.addWidget(QLabel("Index:"))
        ctrl_layout.addWidget(self.index_combo)
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

        # initialize index options
        QTimer.singleShot(0, self.update_index_options)

    def _on_use_selection_toggled(self, _):
        # when using selection, index combo may be irrelevant; still update options
        self.update_index_options()

    def on_auto_data_changed(self):
        # do not auto-plot by default, but update options
        self.update_index_options()

    def on_plot_button(self):
        self.plot(self.current_plot_type)

    def update_index_options(self):
        self.index_combo.clear()
        table_widget = self._get_table_widget()
        if table_widget is None:
            return
        # if using selection, fill index combo with selection summary
        if self.use_selection_cb.isChecked():
            ranges = table_widget.selectedRanges()
            if ranges:
                r = ranges[0]
                summary = f"Selection r{r.topRow()}-r{r.bottomRow()} c{r.leftColumn()}-c{r.rightColumn()}"
                self.index_combo.addItem(summary)
                return
            else:
                # no selection
                self.index_combo.addItem("No selection")
                return

        axis = self.axis_combo.currentText().lower()
        if axis == "column":
            headers = []
            for c in range(table_widget.columnCount()):
                header_item = table_widget.horizontalHeaderItem(c)
                if header_item and header_item.text().strip() != "":
                    headers.append(header_item.text())
                else:
                    headers.append(str(c))
            self.index_combo.addItems(headers if headers else [str(i) for i in range(table_widget.columnCount())])
        else:  # row
            labels = []
            for r in range(table_widget.rowCount()):
                first = table_widget.item(r, 0)
                labels.append(first.text() if first and first.text().strip() != "" else str(r))
            self.index_combo.addItems(labels if labels else [str(i) for i in range(table_widget.rowCount())])

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

        # If using selection and selection exists, respect it
        if self.use_selection_cb.isChecked():
            ranges = table_widget.selectedRanges()
            if not ranges:
                ax.text(0.5, 0.5, "No selection made", ha='center', va='center')
                self.canvas.draw()
                return
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
                    ax.plot(x_positions, y_values, marker='o', label=table_widget.horizontalHeaderItem(col).text() if table_widget.horizontalHeaderItem(col) else f"Col {col}")
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

            # Rectangular selection with multiple cols and rows:
            # Plot each selected column as a separate series across selected rows.
            col_count = right - left + 1
            row_count = bottom - top + 1
            x_labels = []
            series_list = []
            series_labels = []
            # x labels from first column (if present) else row indices
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
                # filter out rows where value is None but keep alignment by skipping them
                y_filtered = []
                x_filtered = []
                for i, v in enumerate(vals):
                    if v is None:
                        continue
                    y_filtered.append(v)
                    x_filtered.append(i)
                if len(y_filtered) == 0:
                    # skip empty series
                    continue
                series_list.append((y_filtered, x_filtered))
                header_item = table_widget.horizontalHeaderItem(c)
                series_labels.append(header_item.text() if header_item and header_item.text().strip() != "" else f"Col {c}")

            if not series_list:
                ax.text(0.5, 0.5, "No numeric data in selection", ha='center', va='center')
                self.canvas.draw()
                return

            # Plot multiple series
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
                    # align each series on the positions they have values for
                    offsets = [pos - 0.4 + j * bar_width + bar_width / 2 for pos in xpos]
                    ax.bar(offsets, yvals, width=bar_width, label=lbl)
                # set xticks to integer positions; mapping labels might be approximate
            # set xticks and labels - show only labels for those x positions that had at least one value
            unique_positions = sorted({p for (_, xp) in series_list for p in xp})
            ax.set_xticks(list(range(len(unique_positions))))
            # try to map integer positions back to row labels; use x_labels indices
            mapped_labels = [x_labels[p] if 0 <= p < len(x_labels) else str(p) for p in unique_positions]
            ax.set_xticklabels(mapped_labels, rotation=45, ha='right')
            ax.set_xlabel("Row (selection)")
            ax.set_ylabel("Value")
            ax.set_title(f"{plot_type.capitalize()} of selection")
            ax.legend()
            self.figure.tight_layout()
            self.canvas.draw()
            return

        # fallback: no selection usage -> original behavior
        x_labels = []
        y_values = []

        if axis == "column":
            col = idx
            if col < 0 or col >= table_widget.columnCount():
                ax.text(0.5, 0.5, "Invalid column", ha='center', va='center')
                self.canvas.draw()
                return
            for r in range(table_widget.rowCount()):
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
                # label: use first column if present, else row index
                first = table_widget.item(r, 0)
                label = first.text().strip() if (first is not None and first.text().strip() != "") else str(r)
                x_labels.append(label)
            x_positions = list(range(len(y_values)))
            if len(y_values) == 0:
                ax.text(0.5, 0.5, "No numeric data in selected column", ha='center', va='center')
                self.canvas.draw()
                return
            if plot_type == "line":
                ax.plot(x_positions, y_values, marker='o')
            elif plot_type == "scatter":
                ax.scatter(x_positions, y_values, c='tab:blue')
            elif plot_type == "bar":
                ax.bar(x_positions, y_values, color='tab:green')
            ax.set_xticks(x_positions)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            ax.set_xlabel("Row")
            ax.set_ylabel(table_widget.horizontalHeaderItem(col).text() if table_widget.horizontalHeaderItem(col) else f"Col {col}")
            ax.set_title(f"{plot_type.capitalize()} of column {col}")
        else:  # row plotting across columns
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
            # filter out None for plotting but keep labels aligned
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