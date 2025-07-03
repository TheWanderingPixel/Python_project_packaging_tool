# Python 项目打包工具

## 项目简介

本工具为 Python 开发者提供一个简洁易用的图形化界面，方便地将任意 Python 项目通过 PyInstaller 进行打包，生成可独立运行的 exe 文件。

## 主要功能

- 项目路径与主程序入口选择
- 图标选择（支持.ico/.png 自动转换）
- 数据文件一同打包
- 打包选项设置（如隐藏终端、单文件、调试、自定义参数）
- 输出目录自定义
- 实时日志高亮美化与精准搜索
- **loading 动画与遮罩层**，打包时界面防误操作
- **配置文件拖拽导入**（支持.json 文件）
- 历史记录与配置保存
- 支持中文路径和文件名
- 主线程安全，杜绝 Qt 跨线程警告

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行 `python main.py`
2. 按界面提示选择项目、主程序、图标、数据文件、输出目录等
3. 设置打包参数，点击"开始打包"
4. 查看日志与 loading 动画，打包完成后可直接打开输出目录

### 配置文件拖拽导入

- 将 .json 配置文件直接拖拽到程序窗口即可快速导入配置
- 导入成功后有提示

## 技术栈

- PyQt5
- PyInstaller
- Python 3.6+

## 目录结构

```
python项目打包工具/
├─ main.py
├─ ui/
│   ├─ main_window.py
│   ├─ widgets.py
│   └─ dialogs.py
├─ core/
│   ├─ packager.py
│   ├─ config.py
│   └─ utils.py
├─ resources/
│   ├─ icons/
│   │   └─ favicon.ico
│   └─ loading/
│       └─ loading.gif
├─ requirements.txt
└─ README.md
```

## 打包命令示例

```bash
pyinstaller -F -w --icon=resources/icons/favicon.ico ^
  --add-data "resources/icons/favicon.ico;resources/icons" ^
  --add-data "resources/loading/loading.gif;resources/loading" ^
  main.py
```

## 截图预览

![效果演示](/image.png)

---

如有建议或问题，欢迎反馈。
