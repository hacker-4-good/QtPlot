import sys 
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget 
from PyQt5.QtCore import Qt 

class TableEditor(QWidget):
    def __init__(self):
        super().__init__() 
        self.setWindowTitle("PyQt Table Editor")
        self.setGeometry(100,100,600,400)

        layout = QVBoxLayout()
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

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

        layout.addWidget(self.table)
        self.setLayout(layout)

if __name__=="__main__":
    app = QApplication(sys.argv)
    editor = TableEditor()
    editor.show() 
    sys.exit(app.exec_())