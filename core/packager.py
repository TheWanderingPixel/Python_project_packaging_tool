import subprocess
import threading
import os
import shutil
import locale

class Packager:
    def __init__(self, py_path, entry, icon, datas, opts, out_dir, log_callback, progress_callback=None, use_pyinstaller_exe=False):
        self.py_path = py_path
        self.entry = entry
        self.icon = icon
        self.datas = datas
        self.opts = opts
        self.out_dir = out_dir
        self.log_callback = log_callback
        self.progress_callback = progress_callback or (lambda x: None)  # 默认为空函数
        self.proc = None
        self.use_pyinstaller_exe = use_pyinstaller_exe

    def build_cmd(self):
        if self.use_pyinstaller_exe:
            pyinstaller_cmd = shutil.which('pyinstaller') or 'pyinstaller'
            cmd = [pyinstaller_cmd]
        else:
            cmd = [self.py_path, '-m', 'pyinstaller']
        if self.icon:
            cmd += ["--icon", self.icon]
        for d in self.datas:
            cmd += ["--add-data", d]
        cmd += self.opts
        cmd += ["--distpath", self.out_dir]
        cmd += ["--log-level", "DEBUG"]
        cmd += [self.entry]
        return cmd

    def cleanup(self):
        # 删除build、__pycache__、.spec等临时文件
        try:
            build_dir = os.path.join(self.py_path, 'build')
            if os.path.isdir(build_dir):
                shutil.rmtree(build_dir)
                self.log_callback('已删除build临时目录')
            pycache_dir = os.path.join(self.py_path, '__pycache__')
            if os.path.isdir(pycache_dir):
                shutil.rmtree(pycache_dir)
                self.log_callback('已删除__pycache__临时目录')
            # 删除.spec文件
            spec_file = os.path.splitext(self.entry)[0] + '.spec'
            spec_path = os.path.join(self.py_path, spec_file)
            if os.path.isfile(spec_path):
                os.remove(spec_path)
                self.log_callback(f'已删除临时文件: {spec_file}')
        except Exception as e:
            self.log_callback(f'清理临时文件失败: {e}')

    def run(self):
        def target():
            cmd = self.build_cmd()
            encoding = locale.getpreferredencoding(False)
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            self.proc = subprocess.Popen(
                cmd, cwd=self.py_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding=encoding, errors='replace', bufsize=1, universal_newlines=True, env=env
            )
            for line in self.proc.stdout:
                # 日志和进度全部用线程安全信号
                self.log_callback(line.rstrip())
                self.progress_callback(line)
            self.proc.wait()
            # print(f"DEBUG: PyInstaller process finished with return code: {self.proc.returncode}")
            if self.proc.returncode == 0:
                self.log_callback("打包成功！")
            else:
                self.log_callback("打包失败，错误码：%d" % self.proc.returncode)
            # 确保发送完成信号
            self.progress_callback("DONE")
            # 发送明确的完成状态消息
            if self.proc.returncode == 0:
                self.log_callback("================ 打包任务完成 ================")
            else:
                self.log_callback("================ 打包任务失败 ================")
            # 添加进程结束的明确信号
            self.log_callback(f"PROCESS_ENDED_{self.proc.returncode}")
            self.cleanup()
        threading.Thread(target=target, daemon=True).start() 