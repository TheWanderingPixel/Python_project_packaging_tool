import subprocess
import threading
import os
import shutil
import locale
import sys

class Packager:
    def __init__(self, py_path, proj_path, entry, icon, datas, opts, out_dir, log_callback, progress_callback=None, use_pyinstaller_exe=False, pyinstaller_path=None):
        self.py_path = py_path
        self.proj_path = proj_path
        self.entry = entry
        self.icon = icon
        self.datas = datas
        self.opts = opts
        self.out_dir = out_dir
        self.log_callback = log_callback
        self.progress_callback = progress_callback or (lambda x: None)  # 默认为空函数
        self.proc = None
        self.use_pyinstaller_exe = use_pyinstaller_exe
        self.pyinstaller_path = pyinstaller_path

    def build_cmd(self):
        # 优先用外部指定的 pyinstaller_path
        if self.pyinstaller_path and os.path.isfile(self.pyinstaller_path):
            pyinstaller_cmd = self.pyinstaller_path
        else:
            pyinstaller_cmd = None
            py_dir = os.path.dirname(self.py_path)
            possible = [
                os.path.join(py_dir, 'Scripts', 'pyinstaller.exe'),
                os.path.join(py_dir, 'pyinstaller.exe')
            ]
            for exe in possible:
                if os.path.isfile(exe):
                    pyinstaller_cmd = exe
                    break
            if not pyinstaller_cmd:
                pyinstaller_cmd = shutil.which('pyinstaller') or 'pyinstaller'
        cmd = [pyinstaller_cmd]
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
        # 删除项目目录下的 build、__pycache__、.spec等临时文件
        try:
            # 项目目录
            proj_dir = self.proj_path
            build_dir = os.path.join(proj_dir, 'build')
            if os.path.isdir(build_dir):
                shutil.rmtree(build_dir)
                self.log_callback('已删除 build 临时目录')
            pycache_dir = os.path.join(proj_dir, '__pycache__')
            if os.path.isdir(pycache_dir):
                shutil.rmtree(pycache_dir)
                self.log_callback('已删除 __pycache__ 临时目录')
            # 删除 .spec 文件
            spec_file = os.path.splitext(os.path.basename(self.entry))[0] + '.spec'
            spec_path = os.path.join(proj_dir, spec_file)
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
            self.log_callback(f"打包命令: {cmd}")
            self.log_callback(f"工作目录: {self.proj_path}")
            self.log_callback(f"目录是否存在: {os.path.isdir(self.proj_path)}")
            self.log_callback(f"python是否存在: {os.path.isfile(self.py_path)}")
            try:
                self.proc = subprocess.Popen(
                    cmd, cwd=self.proj_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding=encoding, errors='replace', bufsize=1, universal_newlines=True, env=env
                )
            except Exception as e:
                self.log_callback(f"Popen异常: {e}")
                return
            for line in self.proc.stdout:
                self.log_callback(line.rstrip())
                self.progress_callback(line)
            self.proc.wait()
            if self.proc.returncode == 0:
                self.log_callback("打包成功！")
            else:
                self.log_callback("打包失败，错误码：%d" % self.proc.returncode)
            self.progress_callback("DONE")
            if self.proc.returncode == 0:
                self.log_callback("================ 打包任务完成 ================")
            else:
                self.log_callback("================ 打包任务失败 ================")
            self.log_callback(f"PROCESS_ENDED_{self.proc.returncode}")
            self.cleanup()
        threading.Thread(target=target, daemon=True).start() 