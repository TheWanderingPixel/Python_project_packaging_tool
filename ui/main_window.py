from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QFileDialog, QListWidget, QCheckBox, QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QInputDialog, QApplication
from PyQt5.QtCore import Qt, QEvent, QTimer, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QMovie, QIcon
from ui.widgets import LogTextEdit
import os
from core.packager import Packager
from core.utils import convert_to_ico
from core.config import save_config, load_config
import json
import shutil
import subprocess
import sys

class MainWindow(QMainWindow):
    log_signal = pyqtSignal(str)
    timer_signal = pyqtSignal(int, object)  # 延迟毫秒数, 回调
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Python项目打包工具")
        self.resize(800, 600)
        # 设置窗口接受拖拽
        self.setAcceptDrops(True)
        # 设置窗口和程序图标
        icon_path = self.resource_path('resources/icons/favicon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.init_ui()
        self.init_signals()
        # 信号连接
        self.log_signal.connect(self.log_edit.append_log)
        self.timer_signal.connect(self.handle_timer)
        self._warned_success_without_end = False
        self._warned_no_end = False

    def handle_timer(self, ms, callback):
        QTimer.singleShot(ms, callback)

    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        # 初始化日志控件
        self.log_edit = LogTextEdit()
        # 必须先初始化所有参数控件
        self.proj_path_edit = QLineEdit()
        self.proj_path_btn = QPushButton("选择目录")
        self.entry_combo = QComboBox()
        self.icon_path_edit = QLineEdit()
        self.icon_btn = QPushButton("选择图标")
        self.icon_convert_btn = QPushButton("图片转ICO")
        self.data_table = QTableWidget(0, 2)
        self.data_table.setHorizontalHeaderLabels(["源文件", "目标路径"])
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.data_add_btn = QPushButton("添加")
        self.data_rm_btn = QPushButton("移除")
        self.cb_noconsole = QCheckBox("隐藏终端窗口")
        self.cb_onefile = QCheckBox("单文件模式")
        self.cb_debug = QCheckBox("调试模式")
        self.custom_args_edit = QLineEdit()
        self.custom_args_edit.setPlaceholderText("其他PyInstaller参数")
        self.out_path_edit = QLineEdit()
        self.out_path_btn = QPushButton("选择目录")
        # 必须先初始化所有操作按钮
        self.clear_log_btn = QPushButton("清空日志")
        self.open_output_btn = QPushButton("打开输出目录")
        self.cancel_btn = QPushButton("取消打包")
        self.start_btn = QPushButton("开始打包")
        self.save_cfg_btn = QPushButton("保存配置")
        self.load_cfg_btn = QPushButton("加载配置")
        self.export_cfg_btn = QPushButton("导出配置")
        self.import_cfg_btn = QPushButton("导入配置")
        self.select_python_btn = QPushButton("选择Python解释器")
        self.install_pyinstaller_btn = QPushButton("一键安装PyInstaller")
        self.select_pyinstaller_btn = QPushButton("选择pyinstaller.exe")
        # 日志区
        log_group = QGroupBox("日志输出")
        log_vbox = QVBoxLayout()
        log_hbox = QHBoxLayout()
        log_hbox.addWidget(self.log_edit.search_bar)
        log_hbox.addWidget(self.log_edit.search_btn)
        log_hbox.addWidget(self.log_edit.prev_btn)
        log_hbox.addWidget(self.log_edit.next_btn)
        log_hbox.addWidget(self.log_edit.export_btn)
        log_vbox.addLayout(log_hbox)
        log_vbox.addWidget(self.log_edit)
        # 添加拖拽提示
        drag_tip = QLabel("💡 提示：可以直接拖拽 .json 配置文件到窗口中进行导入")
        drag_tip.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        drag_tip.setAlignment(Qt.AlignCenter)
        log_vbox.addWidget(drag_tip)
        log_group.setLayout(log_vbox)
        main_layout.addWidget(log_group)
        # 参数区
        param_group = QGroupBox("打包参数")
        param_layout = QVBoxLayout()
        # 项目路径
        proj_layout = QHBoxLayout()
        proj_layout.addWidget(self.proj_path_edit)
        proj_layout.addWidget(self.proj_path_btn)
        param_layout.addLayout(proj_layout)
        # 主程序入口
        entry_layout = QHBoxLayout()
        entry_layout.addWidget(self.entry_combo)
        param_layout.addLayout(entry_layout)
        # 图标
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(self.icon_btn)
        icon_layout.addWidget(self.icon_convert_btn)
        param_layout.addLayout(icon_layout)
        # 数据文件
        data_layout = QHBoxLayout()
        data_layout.addWidget(self.data_table)
        data_btn_layout = QVBoxLayout()
        data_btn_layout.addWidget(self.data_add_btn)
        data_btn_layout.addWidget(self.data_rm_btn)
        data_layout.addLayout(data_btn_layout)
        param_layout.addLayout(data_layout)
        # 打包选项
        opt_layout = QHBoxLayout()
        opt_layout.addWidget(self.cb_noconsole)
        opt_layout.addWidget(self.cb_onefile)
        opt_layout.addWidget(self.cb_debug)
        opt_layout.addWidget(self.custom_args_edit)
        param_layout.addLayout(opt_layout)
        # 输出目录
        out_layout = QHBoxLayout()
        out_layout.addWidget(self.out_path_edit)
        out_layout.addWidget(self.out_path_btn)
        param_layout.addLayout(out_layout)
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)
        # 操作按钮区
        btn_hbox1 = QHBoxLayout()
        btn_hbox1.addWidget(self.start_btn)
        btn_hbox1.addWidget(self.cancel_btn)
        btn_hbox1.addWidget(self.open_output_btn)
        btn_hbox1.addWidget(self.clear_log_btn)
        main_layout.addLayout(btn_hbox1)
        btn_hbox2 = QHBoxLayout()
        btn_hbox2.addWidget(self.save_cfg_btn)
        btn_hbox2.addWidget(self.load_cfg_btn)
        btn_hbox2.addWidget(self.export_cfg_btn)
        btn_hbox2.addWidget(self.import_cfg_btn)
        main_layout.addLayout(btn_hbox2)
        btn_hbox3 = QHBoxLayout()
        btn_hbox3.addWidget(self.select_python_btn)
        btn_hbox3.addWidget(self.install_pyinstaller_btn)
        btn_hbox3.addWidget(self.select_pyinstaller_btn)
        main_layout.addLayout(btn_hbox3)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def init_signals(self):
        self.proj_path_btn.clicked.connect(self.choose_project_dir)
        self.icon_btn.clicked.connect(self.choose_icon_file)
        self.icon_convert_btn.clicked.connect(self.convert_icon)
        self.data_add_btn.clicked.connect(self.add_data_file)
        self.data_rm_btn.clicked.connect(self.remove_data_file)
        self.out_path_btn.clicked.connect(self.choose_output_dir)
        self.start_btn.clicked.connect(self.start_packaging)
        self.clear_log_btn.clicked.connect(self.log_edit.clear_log)
        self.open_output_btn.clicked.connect(self.open_output_dir)
        self.cancel_btn.clicked.connect(self.cancel_packaging)
        self.save_cfg_btn.clicked.connect(self.save_config_action)
        self.load_cfg_btn.clicked.connect(self.load_config_action)
        self.export_cfg_btn.clicked.connect(self.export_config_action)
        self.import_cfg_btn.clicked.connect(self.import_config_action)
        self.select_python_btn.clicked.connect(self.select_python)
        self.install_pyinstaller_btn.clicked.connect(self.install_pyinstaller)
        self.select_pyinstaller_btn.clicked.connect(self.select_pyinstaller_exe)

    def choose_project_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择项目根目录")
        if path:
            self.proj_path_edit.setText(path)
            self.log_signal.emit(f"已选择项目目录: {path}")
            # 自动扫描 .py 文件
            self.entry_combo.clear()
            py_files = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), path)
                        py_files.append(rel_path)
            self.entry_combo.addItems(py_files)
            if py_files:
                self.log_signal.emit(f"已发现主程序入口文件: {py_files}")
            else:
                self.log_signal.emit("未发现任何 .py 文件，请检查项目目录！")

    def choose_icon_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择图标文件", filter="图标文件 (*.ico *.png *.jpg *.jpeg)")
        if file:
            self.icon_path_edit.setText(file)
            self.log_signal.emit(f"已选择图标: {file}")

    def convert_icon(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择图片文件", filter="图片文件 (*.png *.jpg *.jpeg *.bmp)")
        if file:
            ico_path = file.rsplit('.', 1)[0] + '.ico'
            try:
                convert_to_ico(file, ico_path)
                self.icon_path_edit.setText(ico_path)
                QMessageBox.information(self, "转换成功", f"已生成ICO文件: {ico_path}")
                self.log_signal.emit(f"图片已转换为ICO: {ico_path}")
            except Exception as e:
                QMessageBox.warning(self, "转换失败", f"图片转ICO失败: {e}")
                self.log_signal.emit(f"图片转ICO失败: {e}")

    def add_data_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择数据文件或文件夹")
        for f in files:
            row = self.data_table.rowCount()
            self.data_table.insertRow(row)
            self.data_table.setItem(row, 0, QTableWidgetItem(f))
            self.data_table.setItem(row, 1, QTableWidgetItem("."))
            self.log_signal.emit(f"已添加数据文件: {f}")

    def remove_data_file(self):
        rows = set(idx.row() for idx in self.data_table.selectedIndexes())
        for row in sorted(rows, reverse=True):
            self.log_signal.emit(f"已移除数据文件: {self.data_table.item(row,0).text()}")
            self.data_table.removeRow(row)

    def choose_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.out_path_edit.setText(path)
            self.log_signal.emit(f"已选择输出目录: {path}")

    def set_ui_enabled(self, enabled):
        # 项目参数区
        self.proj_path_edit.setEnabled(enabled)
        self.proj_path_btn.setEnabled(enabled)
        self.entry_combo.setEnabled(enabled)
        self.icon_path_edit.setEnabled(enabled)
        self.icon_btn.setEnabled(enabled)
        self.icon_convert_btn.setEnabled(enabled)
        self.data_table.setEnabled(enabled)
        self.data_add_btn.setEnabled(enabled)
        self.data_rm_btn.setEnabled(enabled)
        self.cb_noconsole.setEnabled(enabled)
        self.cb_onefile.setEnabled(enabled)
        self.cb_debug.setEnabled(enabled)
        self.custom_args_edit.setEnabled(enabled)
        self.out_path_edit.setEnabled(enabled)
        self.out_path_btn.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.clear_log_btn.setEnabled(enabled)
        self.open_output_btn.setEnabled(enabled)
        # 取消按钮始终可用
        self.cancel_btn.setEnabled(not enabled)
        # 环境相关按钮也随enabled变化
        self.select_python_btn.setEnabled(enabled)
        self.select_pyinstaller_btn.setEnabled(enabled)
        self.install_pyinstaller_btn.setEnabled(enabled)
        # 禁用关闭窗口（仅打包中才禁用）
        self._block_close = enabled is False and getattr(self, '_in_packaging', False)

    def show_mask(self):
        # centralWidget遮罩修正版：加到centralWidget上，覆盖日志区区域
        cw = self.centralWidget()
        log_rect = self.log_edit.geometry()
        self._mask_widget = QWidget(cw)
        self._mask_widget.setGeometry(log_rect)
        self._mask_widget.setStyleSheet("background:rgba(0,0,0,80);")
        self._mask_widget.setVisible(True)
        self._mask_widget.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self._loading_label = QLabel(self._mask_widget)
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setGeometry(
            (self._mask_widget.width() - 120)//2,
            (self._mask_widget.height() - 120)//2,
            120, 120
        )
        self._loading_label.setScaledContents(True)
        gif_path = self.loading_gif_path()
        if gif_path:
            movie = QMovie(gif_path)
            self._loading_label.setMovie(movie)
            self._movie = movie  # 保持引用，防止被回收
            movie.start()
        else:
            self._loading_label.setText("加载中...")
            self._loading_label.setStyleSheet("color:white;font-size:20px;")
        self._loading_label.show()
        self._mask_widget.show()
        self._mask_widget.raise_()
        self._loading_label.raise_()
        self._loading_label.repaint()

    def hide_mask(self):
        if hasattr(self, '_mask_widget') and self._mask_widget:
            self._mask_widget.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 只有遮罩层可见时才同步大小和位置
        if hasattr(self, '_mask_widget') and self._mask_widget and self._mask_widget.isVisible():
            self._mask_widget.setGeometry(0, 0, self.log_edit.width(), self.log_edit.height())
            size = min(self._mask_widget.width(), self._mask_widget.height(), 120)
            self._loading_label.setGeometry(
                (self._mask_widget.width() - size)//2,
                (self._mask_widget.height() - size)//2,
                size, size
            )
            self._loading_label.setScaledContents(True)

    def resource_path(self, relative_path):
        """获取资源文件的绝对路径，兼容PyInstaller打包和开发环境"""
        import sys, os
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            # ui/xxx.py -> 项目根目录
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def loading_gif_path(self):
        gif_path = self.resource_path('resources/loading/loading.gif')
        if os.path.exists(gif_path):
            return gif_path
        return ''

    def closeEvent(self, event):
        if hasattr(self, '_block_close') and self._block_close:
            QMessageBox.warning(self, "提示", "打包进行中，无法关闭窗口！")
            event.ignore()
        else:
            event.accept()

    def start_packaging(self):
        # 确保状态重置
        self._in_packaging = False
        self._completion_handled = False  # 重置完成状态标志
        self._success_shown = False  # 重置成功对话框显示标志
        self._fail_shown = False  # 重置失败对话框显示标志
        # 设置打包状态
        self._in_packaging = True
        # 参数校验
        proj_path = self.proj_path_edit.text().strip()
        entry = self.entry_combo.currentText().strip()
        icon = self.icon_path_edit.text().strip()
        out_dir = self.out_path_edit.text().strip()
        if not proj_path:
            msg = "项目路径不能为空！"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        if not os.path.isdir(proj_path):
            msg = f"项目路径不存在: {proj_path}"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        if not entry:
            msg = "主程序入口未选择！"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        entry_path = os.path.join(proj_path, entry)
        if not os.path.isfile(entry_path):
            msg = f"主程序入口文件不存在: {entry_path}"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        if icon and not os.path.isfile(icon):
            msg = f"图标文件不存在: {icon}"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        if not out_dir:
            msg = "输出目录不能为空！"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        if not os.path.isdir(out_dir):
            msg = f"输出目录不存在: {out_dir}"
            QMessageBox.warning(self, "参数错误", msg)
            self.log_signal.emit(msg)
            return
        # 数据文件存在性校验
        datas = []
        for row in range(self.data_table.rowCount()):
            src = self.data_table.item(row, 0).text()
            dst = self.data_table.item(row, 1).text()
            if not os.path.exists(src):
                msg = f"数据文件不存在: {src}"
                QMessageBox.warning(self, "参数错误", msg)
                self.log_signal.emit(msg)
                return
            datas.append(f"{src};{dst}")
        # 收集参数
        opts = []
        if self.cb_noconsole.isChecked():
            opts.append('--noconsole')
        if self.cb_onefile.isChecked():
            opts.append('--onefile')
        if self.cb_debug.isChecked():
            opts.append('--debug')
        custom_args = self.custom_args_edit.text().strip()
        if custom_args:
            opts += custom_args.split()
        # 日志和进度回调
        self.log_signal.emit("\n================ 打包任务开始 ================")
        self.log_signal.emit(f"项目目录: {proj_path}")
        self.log_signal.emit(f"主程序入口: {entry}")
        self.log_signal.emit(f"输出目录: {out_dir}")
        if icon:
            self.log_signal.emit(f"图标文件: {icon}")
        if datas:
            self.log_signal.emit(f"数据文件: {datas}")
        self.log_signal.emit("============================================\n")
        self.show_mask()  # 新增：显示loading动画
        def log_cb(msg):
            self.log_signal.emit(msg)
        def progress_cb(msg):
            # 进度回调已移除，仅保留日志输出
            pass
        self.set_ui_enabled(False)
        def final_log_cb(msg):
            log_cb(msg)
            from PyQt5.QtCore import QMetaObject
            if not hasattr(self, '_completion_handled'):
                self._completion_handled = False
            if self._completion_handled:
                return
            def restore_ui():
                self._in_packaging = False
                self._completion_handled = True
                self.set_ui_enabled(True)
                self.hide_mask()
            def show_success():
                from PyQt5.QtWidgets import QMessageBox
                import os
                reply = QMessageBox.information(self, "打包完成", "打包成功！是否打开输出目录？", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    os.startfile(self.out_path_edit.text().strip())
                self.log_signal.emit("\n================ 打包任务完成 ================\n")
            def show_fail():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "打包失败", "打包失败，请检查日志！")
                self.log_signal.emit("\n================ 打包任务失败 ================\n")
                restore_ui()
            def invoke_restore_ui():
                QMetaObject.invokeMethod(self, "restore_ui_slot", Qt.QueuedConnection)
            def invoke_show_success():
                QMetaObject.invokeMethod(self, "show_success_slot", Qt.QueuedConnection)
            def invoke_show_fail():
                QMetaObject.invokeMethod(self, "show_fail_slot", Qt.QueuedConnection)
            # 只在进程真正结束时恢复UI
            if msg.startswith('PROCESS_ENDED_'):
                return_code = msg.split('_')[-1]
                self._completion_handled = True
                if return_code == '0':
                    self.restore_ui_slot()
                    invoke_show_success()
                else:
                    self.restore_ui_slot()
                    invoke_show_fail()
                return
            # 其它分支只做日志提示，不恢复UI
            elif ('打包成功' in msg or 'completed successfully' in msg.lower() or
                'build complete' in msg.lower() or 'build completed' in msg.lower() or
                'done' in msg.lower() or 'finished' in msg.lower() or
                '================ 打包任务完成 ================' in msg):
                if not self._warned_success_without_end:
                    self.log_signal.emit("⚠️ 警告：检测到成功关键字，但未收到进程结束信号，UI未自动恢复！")
                    self._warned_success_without_end = True
            elif ('打包失败' in msg or '================ 打包任务失败 ================' in msg):
                self.log_signal.emit("警告：检测到失败关键字，但未收到进程结束信号，UI未自动恢复！")
            elif '打包进程已被用户取消' in msg:
                self.log_signal.emit("警告：检测到用户取消，但未收到进程结束信号，UI未自动恢复！")
            else:
                if not hasattr(self, '_warned_no_end'):
                    self._warned_no_end = False
                if not self._warned_no_end:
                    self.log_signal.emit("⚠️ 警告：未检测到打包完成信号，UI未自动恢复，请检查日志！")
                    self._warned_no_end = True
        self.packager = Packager(
            py_path=proj_path,
            entry=entry,
            icon=icon if icon else None,
            datas=datas,
            opts=opts,
            out_dir=out_dir,
            log_callback=final_log_cb,
            progress_callback=progress_cb,
            use_pyinstaller_exe=getattr(self, '_use_pyinstaller_exe', False)
        )
        # 安全/快速超时只做日志提示
        def safety_timeout():
            if hasattr(self, '_in_packaging') and self._in_packaging:
                self.log_signal.emit("安全超时：打包未完成，UI未自动恢复，请检查日志！")
        QTimer.singleShot(30000, safety_timeout)
        def quick_timeout():
            if hasattr(self, '_in_packaging') and self._in_packaging:
                self.log_signal.emit("快速超时：打包未完成，UI未自动恢复，请检查日志！")
        QTimer.singleShot(5000, quick_timeout)
        self.packager.run()

    def open_output_dir(self):
        out_dir = self.out_path_edit.text().strip()
        if out_dir and os.path.isdir(out_dir):
            os.startfile(out_dir)
        else:
            QMessageBox.warning(self, "提示", "输出目录无效！")

    def cancel_packaging(self):
        if hasattr(self, 'packager') and self.packager and hasattr(self.packager, 'proc') and self.packager.proc:
            try:
                self.packager.proc.terminate()
                self.log_signal.emit("打包进程已被用户取消。");
                self._in_packaging = False
                self.set_ui_enabled(True)
                self.hide_mask()
            except Exception as e:
                self.log_signal.emit(f"取消失败: {e}")
        else:
            self.log_signal.emit("当前无正在进行的打包任务。")

    def get_config(self):
        # 收集当前界面所有参数
        cfg = {
            'proj_path': self.proj_path_edit.text().strip(),
            'entry': self.entry_combo.currentText().strip(),
            'icon': self.icon_path_edit.text().strip(),
            'out_dir': self.out_path_edit.text().strip(),
            'cb_noconsole': self.cb_noconsole.isChecked(),
            'cb_onefile': self.cb_onefile.isChecked(),
            'cb_debug': self.cb_debug.isChecked(),
            'custom_args': self.custom_args_edit.text().strip(),
            'data_files': [
                {
                    'src': self.data_table.item(row, 0).text(),
                    'dst': self.data_table.item(row, 1).text()
                } for row in range(self.data_table.rowCount())
            ]
        }
        return cfg

    def set_config(self, cfg):
        self.proj_path_edit.setText(cfg.get('proj_path', ''))
        self.icon_path_edit.setText(cfg.get('icon', ''))
        self.out_path_edit.setText(cfg.get('out_dir', ''))
        self.cb_noconsole.setChecked(cfg.get('cb_noconsole', False))
        self.cb_onefile.setChecked(cfg.get('cb_onefile', False))
        self.cb_debug.setChecked(cfg.get('cb_debug', False))
        self.custom_args_edit.setText(cfg.get('custom_args', ''))
        # 入口文件下拉框刷新
        proj_path = cfg.get('proj_path', '')
        if proj_path and os.path.isdir(proj_path):
            self.entry_combo.clear()
            py_files = []
            for root, dirs, files in os.walk(proj_path):
                for file in files:
                    if file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), proj_path)
                        py_files.append(rel_path)
            self.entry_combo.addItems(py_files)
            entry = cfg.get('entry', '')
            idx = self.entry_combo.findText(entry)
            if idx >= 0:
                self.entry_combo.setCurrentIndex(idx)
        # 数据文件表格
        self.data_table.setRowCount(0)
        for item in cfg.get('data_files', []):
            row = self.data_table.rowCount()
            self.data_table.insertRow(row)
            self.data_table.setItem(row, 0, QTableWidgetItem(item['src']))
            self.data_table.setItem(row, 1, QTableWidgetItem(item['dst']))

    def save_config_action(self):
        cfg = self.get_config()
        save_config(cfg)
        self.log_signal.emit("已保存当前配置到历史记录。")

    def load_config_action(self):
        cfg = load_config()
        if cfg:
            self.set_config(cfg)
            self.log_signal.emit("已加载历史记录配置。")
        else:
            self.log_signal.emit("未找到历史记录配置。")

    def export_config_action(self):
        cfg = self.get_config()
        file, _ = QFileDialog.getSaveFileName(self, "导出配置", filter="JSON文件 (*.json)")
        if file:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.log_signal.emit(f"已导出配置到: {file}")

    def import_config_action(self):
        file, _ = QFileDialog.getOpenFileName(self, "导入配置", filter="JSON文件 (*.json)")
        if file:
            with open(file, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.set_config(cfg)
            self.log_signal.emit(f"已导入配置: {file}")

    def check_env(self):
        pyinstaller_path = shutil.which('pyinstaller')
        self.log_signal.emit(f"pyinstaller_path: {pyinstaller_path}")
        if not pyinstaller_path:
            # 额外检测常见环境的Scripts目录
            possible_dirs = []
            for base in [os.getcwd(), os.path.expanduser('~')]:
                for venv_dir in ['.venv', 'venv', 'env', 'Scripts']:
                    d = os.path.join(base, venv_dir)
                    exe = os.path.join(d, 'pyinstaller.exe')
                    if os.path.exists(exe):
                        possible_dirs.append(exe)
            if possible_dirs:
                pyinstaller_path = possible_dirs[0]
                self.log_signal.emit(f'在其他目录发现pyinstaller: {pyinstaller_path}')
        self._use_pyinstaller_exe = False
        pyinstaller_ok = False
        if pyinstaller_path:
            try:
                result = subprocess.run([pyinstaller_path, '--version'], capture_output=True, text=True)
                pyinstaller_ok = result.returncode == 0
                self.log_signal.emit(f"检测命令: {pyinstaller_path} --version")
                self.log_signal.emit(f"检测输出: {result.stdout.strip()} {result.stderr.strip()}")
                if pyinstaller_ok:
                    self._use_pyinstaller_exe = True
                    self._pyinstaller_path = pyinstaller_path
            except Exception as e:
                self.log_signal.emit(f"检测异常: {e}")
                pyinstaller_ok = False
        msg = ''
        if not pyinstaller_ok:
            msg += '未检测到PyInstaller，点击"一键安装PyInstaller"或"选择pyinstaller.exe"手动指定。'
        if msg:
            QMessageBox.critical(self, '环境检测失败', msg)
            self.start_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
        else:
            self.set_ui_enabled(True)
            self.start_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)

    def select_python(self):
        # 弹出可选python列表
        items = self._python_candidates if hasattr(self, '_python_candidates') else []
        items = [p for p in items if p]
        if items:
            item, ok = QInputDialog.getItem(self, "选择Python解释器", "可用环境:", items, 0, False)
            if ok and item:
                self.python_path = item
                self.log_signal.emit(f"已选择Python解释器: {item}")
                self.check_env()
                return
        # 兜底：手动选择
        file, _ = QFileDialog.getOpenFileName(self, "选择Python解释器", filter="可执行文件 (*.exe)")
        if file:
            self.python_path = file
            self.log_signal.emit(f"已选择Python解释器: {file}")
            self.check_env()

    def install_pyinstaller(self):
        if not hasattr(self, 'python_path') or not self.python_path:
            QMessageBox.warning(self, "提示", "请先选择Python解释器！")
            return
        self.log_signal.emit("正在安装PyInstaller...")
        try:
            result = subprocess.run([self.python_path, '-m', 'pip', 'install', 'pyinstaller'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_signal.emit("PyInstaller安装成功！")
                # 安装后立即检测
                check_result = subprocess.run([self.python_path, '-m', 'pyinstaller', '--version'], capture_output=True, text=True)
                self.log_signal.emit(f"检测命令: {self.python_path} -m pyinstaller --version")
                self.log_signal.emit(f"检测结果: {check_result.stdout.strip()} {check_result.stderr.strip()}")
                if check_result.returncode == 0:
                    QMessageBox.information(self, "成功", "PyInstaller安装并检测成功！")
                else:
                    QMessageBox.warning(self, "警告", "PyInstaller安装后检测失败，请检查Python环境！")
                self.check_env()
            else:
                self.log_signal.emit(f"PyInstaller安装失败: {result.stderr}")
                QMessageBox.warning(self, "失败", "PyInstaller安装失败，请检查日志！")
        except Exception as e:
            self.log_signal.emit(f"安装异常: {e}")
            QMessageBox.warning(self, "失败", f"安装异常: {e}")

    def select_pyinstaller_exe(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择pyinstaller.exe", filter="可执行文件 (*.exe)")
        if file:
            self._pyinstaller_path = file
            self._use_pyinstaller_exe = True
            self.log_signal.emit(f"已手动指定pyinstaller.exe: {file}")
            # 立即检测
            try:
                result = subprocess.run([file, '--version'], capture_output=True, text=True)
                ok = result.returncode == 0
                self.log_signal.emit(f"检测命令: {file} --version")
                self.log_signal.emit(f"检测输出: {result.stdout.strip()} {result.stderr.strip()}")
                if ok:
                    self.set_ui_enabled(True)
                    self.start_btn.setEnabled(True)
                    self.cancel_btn.setEnabled(True)
                    QMessageBox.information(self, "成功", "PyInstaller检测通过！")
                else:
                    QMessageBox.warning(self, "失败", "PyInstaller检测失败，请检查文件！")
            except Exception as e:
                self.log_signal.emit(f"检测异常: {e}")
                QMessageBox.warning(self, "失败", f"PyInstaller检测异常: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_env_checked'):
            self.check_env()
            self._env_checked = True
    
    @pyqtSlot()
    def restore_ui_slot(self):
        self._in_packaging = False
        self._completion_handled = True
        self.set_ui_enabled(True)
        self.hide_mask()
    
    @pyqtSlot()
    def show_success_slot(self):
        """在主线程中显示成功对话框的槽函数"""
        if hasattr(self, '_success_shown') and self._success_shown:
            return
        if not hasattr(self, '_in_packaging') or not self._in_packaging:
            return
        self._success_shown = True
        from PyQt5.QtWidgets import QMessageBox
        import os
        reply = QMessageBox.information(self, "打包完成", "打包成功！是否打开输出目录？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            os.startfile(self.out_path_edit.text().strip())
        self.log_signal.emit("\n================ 打包任务完成 ================\n")
    
    @pyqtSlot()
    def show_fail_slot(self):
        """在主线程中显示失败对话框的槽函数"""
        if hasattr(self, '_fail_shown') and self._fail_shown:
            return
        if not hasattr(self, '_in_packaging') or not self._in_packaging:
            return
        self._fail_shown = True
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "打包失败", "打包失败，请检查日志！")
        self.log_signal.emit("\n================ 打包任务失败 ================\n")
        self.restore_ui_slot()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.json'):
                    event.acceptProposedAction()
                    self.setWindowTitle("Python项目打包工具 - 拖拽配置文件到此处")
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.json'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragLeaveEvent(self, event):
        self.setWindowTitle("Python项目打包工具")
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.json'):
                    self.log_signal.emit(f"检测到配置文件拖拽: {file_path}")
                    self.import_config_from_file(file_path)
                    event.acceptProposedAction()
                    self.setWindowTitle("Python项目打包工具")
                    return
        event.ignore()
    
    def import_config_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.set_config(cfg)
            self.log_signal.emit(f"已成功导入配置文件: {file_path}")
            QMessageBox.information(self, "导入成功", f"已成功导入配置文件:\n{file_path}")
        except FileNotFoundError:
            self.log_signal.emit(f"配置文件不存在: {file_path}")
            QMessageBox.warning(self, "导入失败", f"配置文件不存在:\n{file_path}")
        except json.JSONDecodeError as e:
            self.log_signal.emit(f"配置文件格式错误: {e}")
            QMessageBox.warning(self, "导入失败", f"配置文件格式错误:\n{str(e)}")
        except Exception as e:
            self.log_signal.emit(f"导入配置文件失败: {e}")
            QMessageBox.warning(self, "导入失败", f"导入配置文件时发生错误:\n{str(e)}")

 