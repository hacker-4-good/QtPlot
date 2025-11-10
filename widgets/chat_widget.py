from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from widgets.table_editor import TableEditor
from widgets.plot_widget import PlotWidget
import dspy
from dotenv import load_dotenv
import io
import csv
import traceback
import os 

load_dotenv()

llm = dspy.LM(model="ollama/llama3.2:latest")
dspy.settings.configure(lm=llm)

class PlotInsightSignature(dspy.Signature):
    """Give fast response to the user's query"""
    plot_figure = dspy.InputField(desc="This will contain Plotly fig of the plot")
    data = dspy.InputField(desc="This will provide dataset in string format")
    user_query = dspy.InputField(desc="User's query")
    insights = dspy.OutputField(desc="Provide elaborated insight about the plot in MARKDOWN")

# ---------- Worker thread class ----------
class ModelWorker(QThread):
    finished = Signal(str)  # emits response text

    def __init__(self, user_query, data_text, plot_bytes):
        super().__init__()
        self.user_query = user_query
        self.data_text = data_text
        self.plot_bytes = plot_bytes

    def run(self):
        try:
            model = dspy.ChainOfThought(signature=PlotInsightSignature)
            result = model(
                plot_figure=self.plot_bytes,
                data=self.data_text,
                user_query=self.user_query
            )
            text = result.insights or "Model returned no insights."
        except Exception as e:
            text = f"Error querying model:\n{traceback.format_exc()}"
        self.finished.emit(text)

# ---------- Main Chat Widget ----------
class ChatWidget(QWidget):
    def __init__(self, parent=None, table_editor: TableEditor | None = None, plot_widget: PlotWidget | None = None):
        super().__init__(parent)
        self.table_editor = table_editor
        self.plot_widget = plot_widget
        self.worker = None

        layout = QVBoxLayout(self)
        self.conv = QTextBrowser()
        layout.addWidget(self.conv)

        opts_layout = QHBoxLayout()
        self.include_data_cb = QCheckBox("Include table data")
        self.include_plot_cb = QCheckBox("Include current plot image")
        self.include_data_cb.setChecked(True)
        opts_layout.addWidget(self.include_data_cb)
        opts_layout.addWidget(self.include_plot_cb)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.send_btn = QPushButton("Send")
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        self.send_btn.clicked.connect(self.on_send)
        self.input_edit.returnPressed.connect(self.on_send)

    def append_message(self, sender: str, text: str):
        self.conv.append(f"<b>{sender}:</b> {text}")

    def table_to_csv_text(self) -> str:
        tw = getattr(self.table_editor, "table", None)
        if not isinstance(tw, QTableWidget):
            return ""
        output = io.StringIO()
        writer = csv.writer(output)
        headers = [tw.horizontalHeaderItem(c).text() if tw.horizontalHeaderItem(c) else f"Col{c}"
                   for c in range(tw.columnCount())]
        writer.writerow(headers)
        for r in range(tw.rowCount()):
            row = [tw.item(r, c).text() if tw.item(r, c) else "" for c in range(tw.columnCount())]
            writer.writerow(row)
        return output.getvalue()

    def capture_plot_png(self) -> bytes | None:
        pw = self.plot_widget
        if not isinstance(pw, PlotWidget):
            return None
        buf = io.BytesIO()
        try:
            pw.figure.savefig(buf, format="png", bbox_inches="tight")
            return buf.getvalue()
        except Exception:
            return None

    def on_send(self):
        user_text = self.input_edit.text().strip()
        if not user_text:
            return

        self.append_message("User", user_text)
        self.append_message("System", "<i>🧠 Thinking... please wait</i>")

        data_text = self.table_to_csv_text() if self.include_data_cb.isChecked() else None
        plot_bytes = self.capture_plot_png() if self.include_plot_cb.isChecked() else None

        # Disable input during processing
        self.send_btn.setEnabled(False)
        self.input_edit.setEnabled(False)

        # Start worker thread
        self.worker = ModelWorker(user_text, data_text, plot_bytes)
        self.worker.finished.connect(self.on_model_finished)
        self.worker.start()

    def on_model_finished(self, response_text: str):
        # Re-enable UI
        self.send_btn.setEnabled(True)
        self.input_edit.setEnabled(True)

        # Remove loader and show output
        self.conv.append(f"<b>Chatbot:</b> {response_text}")
        self.input_edit.clear()
