from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from widgets.table_editor import TableEditor
from widgets.plot_widget import PlotWidget
import dspy
from dotenv import load_dotenv
import io
import csv
load_dotenv()

llm = dspy.LM(model="ollama/llama3.2:latest")
dspy.settings.configure(lm=llm)


class PlotInsightSignature(dspy.Signature):
    """
    This signature aims to fetch the required insight for given plot
    **start by explaining the domain of plot**
    -> You are free to elaborate based upon your need just focus on respective domain of question
    -> you're free to use maths calculation on data if user such query
    -> You also get the tabular data and have to perform statistical analysis on the same
    """
    plot_figure = dspy.InputField(desc = "This will contain Plotly fig of the plot")
    data = dspy.InputField(desc="This will provide you the dataset on which analysis to be done in string format")
    user_query = dspy.InputField(desc="User's query")
    insights = dspy.OutputField(desc="Provide elaborated insight about the plot possibly in MARKDOWN and also have to do calculation")

class ChatWidget(QWidget):
    """
    Simple chatbot UI that can send the current table and/or current plot to dspy for insights.
    Uses Signature defined above if dspy.run is available, otherwise attempts to call llm directly.
    """
    def __init__(self, parent=None, table_editor: TableEditor | None = None, plot_widget: PlotWidget | None = None):
        super().__init__(parent)
        self.table_editor = table_editor
        self.plot_widget = plot_widget

        layout = QVBoxLayout(self)

        # conversation display
        self.conv = QTextBrowser()
        layout.addWidget(self.conv)

        # controls: include data/plot checkboxes
        opts_layout = QHBoxLayout()
        self.include_data_cb = QCheckBox("Include table data")
        self.include_plot_cb = QCheckBox("Include current plot image")
        self.include_data_cb.setChecked(True)
        opts_layout.addWidget(self.include_data_cb)
        opts_layout.addWidget(self.include_plot_cb)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        # input area
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
        headers = []
        for c in range(tw.columnCount()):
            hi = tw.horizontalHeaderItem(c)
            headers.append(hi.text() if hi else f"Col{c}")
        writer.writerow(headers)
        for r in range(tw.rowCount()):
            row = []
            for c in range(tw.columnCount()):
                item = tw.item(r, c)
                row.append(item.text() if item else "")
            writer.writerow(row)
        return output.getvalue()

    def capture_plot_png(self) -> bytes | None:
        pw = self.plot_widget
        if not isinstance(pw, PlotWidget):
            return None
        buf = io.BytesIO()
        try:
            # save current figure to PNG bytes
            pw.figure.savefig(buf, format="png", bbox_inches="tight")
            return buf.getvalue()
        except Exception:
            return None

    def on_send(self):
        user_text = self.input_edit.text().strip()
        if user_text == "":
            return
        self.append_message("User", user_text)

        # prepare data and plot if requested
        data_text = None
        plot_bytes = None
        if self.include_data_cb.isChecked() and self.table_editor is not None:
            data_text = self.table_to_csv_text()
        if self.include_plot_cb.isChecked() and self.plot_widget is not None:
            plot_bytes = self.capture_plot_png()

        # send to dspy/signature if available, otherwise attempt direct call
        self.append_message("System", "Querying model...")
        QApplication.processEvents()

        response_text = None
        try:
            model = dspy.ChainOfThought(signature=PlotInsightSignature)
            response_text = model(plot_figure = plot_bytes, data = data_text, user_query=user_text).insights
        except Exception as e:
            response_text = f"Error querying model: {e}"

        if not response_text:
            response_text = "Model returned no insights."

        self.append_message("Chatbot", response_text)
        self.input_edit.clear()