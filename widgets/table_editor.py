from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import csv


class TableEditor(QWidget):
    structure_changed = Signal()
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # toolbar for adding/removing rows/columns
        toolbar = QHBoxLayout()
        add_row_btn = QPushButton("Add Row")
        add_col_btn = QPushButton("Add Column")
        remove_row_btn = QPushButton("Remove Row")
        remove_col_btn = QPushButton("Remove Column")
        toolbar.addWidget(add_row_btn)
        toolbar.addWidget(add_col_btn)
        toolbar.addWidget(remove_row_btn)
        toolbar.addWidget(remove_col_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setRowCount(3)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Age"])

        self.table.setItem(0,0,QTableWidgetItem("Alice"))
        self.table.setItem(0,1,QTableWidgetItem("30"))
        self.table.setItem(1,0,QTableWidgetItem("Bob"))
        self.table.setItem(1,1,QTableWidgetItem("24"))
        self.table.setItem(2,0,QTableWidgetItem("Charlie"))
        self.table.setItem(2,1,QTableWidgetItem("35"))

        # allow multi-cell selection with mouse
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)

        # make items editable
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

        layout.addWidget(self.table)

        # connections
        add_row_btn.clicked.connect(self.add_row)
        add_col_btn.clicked.connect(self.add_column)
        remove_row_btn.clicked.connect(self.remove_selected_row)
        remove_col_btn.clicked.connect(self.remove_selected_column)
        self.table.itemChanged.connect(self._on_item_changed)
        # emit structure_changed on selection changes so plot widget can react if needed
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_item_changed(self, item: QTableWidgetItem):
        # ensure editable flag kept and emit data_changed
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.data_changed.emit()

    def _on_selection_changed(self):
        # Notify that structure/selection changed (used by plot widget's "use selection")
        self.structure_changed.emit()

    def add_row(self):
        r = self.table.rowCount()
        self.table.setRowCount(r + 1)
        for c in range(self.table.columnCount()):
            self.table.setItem(r, c, QTableWidgetItem(""))
        self._set_items_editable_in_row(r)
        self.structure_changed.emit()

    def add_column(self):
        c = self.table.columnCount()
        self.table.setColumnCount(c + 1)
        default_name = f"Col {c}"
        text, ok = QInputDialog.getText(self, "New column", "Column name:", text=default_name)
        header = text if ok and text.strip() != "" else default_name
        headers = [self.table.horizontalHeaderItem(i).text() if self.table.horizontalHeaderItem(i) else f"Col {i}" for i in range(c)]
        headers.append(header)
        self.table.setHorizontalHeaderLabels(headers)
        # fill items
        for r in range(self.table.rowCount()):
            self.table.setItem(r, c, QTableWidgetItem(""))
        self.structure_changed.emit()

    def remove_selected_row(self):
        selected = self.table.currentRow()
        if selected >= 0:
            self.table.removeRow(selected)
            self.structure_changed.emit()

    def remove_selected_column(self):
        selected = self.table.currentColumn()
        if selected >= 0:
            self.table.removeColumn(selected)
            self.structure_changed.emit()

    def _set_items_editable_in_row(self, r):
        for c in range(self.table.columnCount()):
            item = self.table.item(r, c)
            if item:
                item.setFlags(item.flags() | Qt.ItemIsEditable)

    def load_csv(self, filepath: str, has_header: bool = True, encoding: str = "utf-8"):
        """
        Load CSV from filepath into the table.
        If has_header is True, the first CSV row becomes horizontal headers.
        """
        try:
            with open(filepath, newline="", encoding=encoding) as f:
                reader = csv.reader(f)
                rows = [row for row in reader]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV:\n{e}")
            return

        if not rows:
            QMessageBox.information(self, "Empty", "CSV file is empty.")
            return

        # determine max columns in case of ragged rows
        max_cols = max(len(r) for r in rows)

        if has_header:
            headers = rows[0] + [""] * (max_cols - len(rows[0]))
            data_rows = rows[1:]
        else:
            headers = [f"Col {i}" for i in range(max_cols)]
            data_rows = rows

        self.table.setColumnCount(max_cols)
        self.table.setRowCount(len(data_rows))
        self.table.setHorizontalHeaderLabels(headers)

        for r, row in enumerate(data_rows):
            for c in range(max_cols):
                text = row[c] if c < len(row) else ""
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

        self.structure_changed.emit()
        self.data_changed.emit()