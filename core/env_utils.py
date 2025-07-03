import os
import sys
import json
import subprocess

def get_config_path():
    # 判断是否为 PyInstaller 打包后的环境
    if hasattr(sys, '_MEIPASS'):
        # exe 运行时，放在用户主目录
        return os.path.join(os.path.expanduser('~'), 'config.json')
    else:
        # 开发环境，放在项目根目录
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')


def save_python_path(python_path: str):
    """保存用户选择的 Python 解释器路径"""
    config_path = get_config_path()
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
    config['python_path'] = python_path
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_python_path() -> str:
    """读取已保存的 Python 解释器路径"""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
            return config.get('python_path')
        except Exception:
            return None


def check_pyinstaller(python_path: str) -> bool:
    """检查指定 Python 环境下 PyInstaller 是否可用"""
    try:
        result = subprocess.run(
            [python_path, '-m', 'PyInstaller', '--version'],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def install_pyinstaller(python_path: str) -> bool:
    """自动安装 PyInstaller"""
    try:
        result = subprocess.run(
            [python_path, '-m', 'pip', 'install', 'pyinstaller'],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except Exception:
        return False


def save_pyinstaller_path(pyinstaller_path: str):
    config_path = get_config_path()
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
    config['pyinstaller_path'] = pyinstaller_path
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_pyinstaller_path() -> str:
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
            return config.get('pyinstaller_path')
        except Exception:
            return None 