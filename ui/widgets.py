import threading
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QTextCursor

class LogTextEdit(QTextEdit):
    append_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(120)
        self.setStyleSheet("background:#f8f8f8;font-family:Consolas;font-size:13px;")
        # 搜索栏和导出按钮
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索日志...")
        self.search_btn = QPushButton("搜索")
        self.prev_btn = QPushButton("上一个")
        self.next_btn = QPushButton("下一个")
        self.export_btn = QPushButton("导出日志")
        self.search_btn.clicked.connect(self.search_log)
        self.prev_btn.clicked.connect(self.search_prev)
        self.next_btn.clicked.connect(self.search_next)
        self.export_btn.clicked.connect(self.export_log)
        self._last_search = ''
        self._search_results = []  # 匹配QTextCursor列表
        self._search_index = -1    # 当前高亮索引
        self.append_signal.connect(self.append_log)
        self.textChanged.connect(self._reset_search)

    def thread_safe_append(self, text):
        self.append_signal.emit(text)

    def append_log(self, text):
        assert threading.current_thread() == threading.main_thread(), "append_log只能在主线程调用"
        fmt = QTextCharFormat()
        icon = ''
        lower = text.lower()
        # ERROR/FAILED
        if any(w in lower for w in ["error", "failed", "失败", "traceback"]):
            fmt.setForeground(QColor("#ff4d4f"))  # 红色
            fmt.setFontWeight(QFont.Bold)
            icon = '❌ '
        # WARNING
        elif any(w in lower for w in ["warn", "警告", "warning"]):
            fmt.setForeground(QColor("#faad14"))  # 橙色
            fmt.setFontWeight(QFont.Bold)
            icon = '⚠️ '
        # SUCCESS
        elif any(w in lower for w in ["success", "打包成功", "build complete", "completed successfully"]):
            fmt.setForeground(QColor("#52c41a"))  # 绿色
            fmt.setFontWeight(QFont.Bold)
            icon = '✅ '
        # DEBUG
        elif "debug" in lower:
            fmt.setForeground(QColor("#888888"))  # 灰色
            icon = '🐞 '
        # INFO
        elif "info" in lower:
            fmt.setForeground(QColor("#1890ff"))  # 蓝色
            icon = 'ℹ️ '
        else:
            fmt.setForeground(QColor("#222"))
        self.moveCursor(self.textCursor().End)
        self.setCurrentCharFormat(fmt)
        self.append(icon + text)
        self.moveCursor(self.textCursor().End)

    def clear_log(self):
        assert threading.current_thread() == threading.main_thread(), "clear_log只能在主线程调用"
        self.clear()

    def _reset_search(self):
        assert threading.current_thread() == threading.main_thread(), "_reset_search只能在主线程调用"
        self._search_results = []
        self._search_index = -1
        self._last_search = ''
        self._clear_extra_selection()

    def search_log(self):
        assert threading.current_thread() == threading.main_thread(), "search_log只能在主线程调用"
        keyword = self.search_bar.text().strip()
        if not keyword:
            self._reset_search()
            return
        self._search_results = []
        doc = self.document()
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(keyword, cursor)
            if cursor.isNull():
                break
            self._search_results.append(QTextCursor(cursor))
        if not self._search_results:
            self._search_index = -1
            self._clear_extra_selection()
            return
        self._search_index = 0
        self._highlight_all(keyword)
        self._move_to_result(self._search_index, keyword)
        self._last_search = keyword

    def search_next(self):
        assert threading.current_thread() == threading.main_thread(), "search_next只能在主线程调用"
        if not self._search_results:
            self.search_log()
            return
        self._search_index = (self._search_index + 1) % len(self._search_results)
        self._move_to_result(self._search_index, self._last_search)

    def search_prev(self):
        assert threading.current_thread() == threading.main_thread(), "search_prev只能在主线程调用"
        if not self._search_results:
            self.search_log()
            return
        self._search_index = (self._search_index - 1 + len(self._search_results)) % len(self._search_results)
        self._move_to_result(self._search_index, self._last_search)

    def _move_to_result(self, idx, keyword):
        assert threading.current_thread() == threading.main_thread(), "_move_to_result只能在主线程调用"
        if not self._search_results or idx < 0 or idx >= len(self._search_results):
            return
        cursor = self._search_results[idx]
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _highlight_all(self, keyword):
        assert threading.current_thread() == threading.main_thread(), "_highlight_all只能在主线程调用"
        extraSelections = []
        for cursor in self._search_results:
            selection = QTextEdit.ExtraSelection()
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#ffe58f"))
            selection.format = fmt
            selection.cursor = cursor
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def _clear_extra_selection(self):
        assert threading.current_thread() == threading.main_thread(), "_clear_extra_selection只能在主线程调用"
        self.setExtraSelections([])

    def export_log(self):
        assert threading.current_thread() == threading.main_thread(), "export_log只能在主线程调用"
        file, _ = QFileDialog.getSaveFileName(self, "导出日志", filter="文本文件 (*.txt)")
        if file:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText()) 