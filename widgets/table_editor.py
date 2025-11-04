from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QAbstractItemView, QTableWidgetItem,
    QInputDialog, QMessageBox, QProgressBar, QLabel
)
import csv
import os


# ---------------- Worker Thread for Background CSV Loading ----------------
class CSVLoaderWorker(QObject):
    chunk_loaded = Signal(list)   # Emits list of rows (list[list[str]])
    finished = Signal()
    error = Signal(str)

    def __init__(self, filepath, has_header=True, encoding="utf-8", chunk_size=1000):
        super().__init__()
        self.filepath = filepath
        self.has_header = has_header
        self.encoding = encoding
        self.chunk_size = chunk_size
        self._running = True

    def stop(self):
        """Stop loading early (if user cancels)."""
        self._running = False

    def run(self):
        """Runs in background thread, loads file chunk by chunk."""
        try:
            with open(self.filepath, newline="", encoding=self.encoding) as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                if first_row is None:
                    self.error.emit("Empty CSV file.")
                    return

                if self.has_header:
                    headers = first_row
                else:
                    headers = [f"Col {i}" for i in range(len(first_row))]
                    self.chunk_loaded.emit([first_row])

                # Emit header as first chunk
                self.chunk_loaded.emit(["__HEADER__", headers])

                chunk = []
                for row in reader:
                    if not self._running:
                        break
                    chunk.append(row)
                    if len(chunk) >= self.chunk_size:
                        self.chunk_loaded.emit(chunk)
                        chunk = []

                # Emit last partial chunk
                if chunk:
                    self.chunk_loaded.emit(chunk)

                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ---------------- Table Editor UI ----------------
class TableEditor(QWidget):
    structure_changed = Signal()
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Toolbar
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

        # Progress info
        self.status_label = QLabel("")
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.hide()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)

        # Table
        self.table = QTableWidget()
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        layout.addWidget(self.table)

        # Connections
        add_row_btn.clicked.connect(self.add_row)
        add_col_btn.clicked.connect(self.add_column)
        remove_row_btn.clicked.connect(self.remove_selected_row)
        remove_col_btn.clicked.connect(self.remove_selected_column)

        self.table.itemChanged.connect(lambda _: self.data_changed.emit())

        # Thread-related attributes
        self._thread = None
        self._worker = None

    # ----------------------------------------------------------------------
    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c in range(self.table.columnCount()):
            self.table.setItem(r, c, QTableWidgetItem(""))

    def add_column(self):
        c = self.table.columnCount()
        text, ok = QInputDialog.getText(self, "New column", "Column name:", text=f"Col {c}")
        name = text if ok and text.strip() else f"Col {c}"
        self.table.insertColumn(c)
        headers = [self.table.horizontalHeaderItem(i).text() if self.table.horizontalHeaderItem(i) else f"Col {i}" for i in range(c)]
        headers.append(name)
        self.table.setHorizontalHeaderLabels(headers)

    def remove_selected_row(self):
        i = self.table.currentRow()
        if i >= 0:
            self.table.removeRow(i)

    def remove_selected_column(self):
        i = self.table.currentColumn()
        if i >= 0:
            self.table.removeColumn(i)

    # ----------------------------------------------------------------------
    def load_csv_in_background(self, filepath: str, has_header=True, encoding="utf-8", chunk_size=2000):
        """Load CSV in background thread without freezing UI."""
        if not os.path.exists(filepath):
            QMessageBox.critical(self, "Error", f"File not found: {filepath}")
            return

        # Clear table and start progress
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.status_label.setText(f"Loading {os.path.basename(filepath)} ...")
        self.progress.show()

        # Start background thread
        self._thread = QThread()
        self._worker = CSVLoaderWorker(filepath, has_header, encoding, chunk_size)
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.chunk_loaded.connect(self._append_csv_chunk)
        self._worker.finished.connect(self._on_load_finished)
        self._worker.error.connect(self._on_load_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # Run
        self._thread.start()

    # ----------------------------------------------------------------------
    def _append_csv_chunk(self, chunk):
        """Add chunk of rows to table incrementally."""
        if not chunk:
            return

        # Header chunk
        if len(chunk) == 2 and chunk[0] == "__HEADER__":
            headers = chunk[1]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            return

        # Regular data rows
        start = self.table.rowCount()
        self.table.setRowCount(start + len(chunk))
        col_count = self.table.columnCount()

        for i, row in enumerate(chunk):
            for j in range(col_count):
                text = row[j] if j < len(row) else ""
                self.table.setItem(start + i, j, QTableWidgetItem(text))

        self.data_changed.emit()
        self.status_label.setText(f"Loaded {self.table.rowCount()} rows...")

    # ----------------------------------------------------------------------
    def _on_load_finished(self):
        self.progress.hide()
        self.status_label.setText(f"Loaded all {self.table.rowCount()} rows ✅")
        self.data_changed.emit()

    def _on_load_error(self, msg):
        self.progress.hide()
        QMessageBox.critical(self, "Error", f"Failed to load CSV:\n{msg}")

