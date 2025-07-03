from PyQt5.QtWidgets import QFileDialog, QMessageBox

# 可扩展自定义对话框
class FileSelectDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFileMode(QFileDialog.Directory)

class IconConvertDialog(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图标转换")
        self.setText("图片已自动转换为ico格式！") 