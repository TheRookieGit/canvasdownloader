# Windows版本打包说明

## 环境要求

1. Python 3.8或更高版本
2. 安装必要的依赖：
```bash
pip install canvassyncer PyQt5 pyinstaller
```

## 打包步骤

1. 下载源代码并进入项目目录

2. 确保有以下文件：
   - `canvas_downloader_gui.py`
   - `canvas_downloader_win.spec`
   - `setup.iss`
   - `app_icon.ico`（Windows图标文件）

3. 使用PyInstaller打包：
```bash
pyinstaller canvas_downloader_win.spec
```

4. 使用Inno Setup创建安装包：
   - 下载并安装 [Inno Setup](https://jrsoftware.org/isdl.php)
   - 打开 `setup.iss` 文件
   - 点击 "Build" > "Compile"

5. 打包完成后，安装包将位于 `installer` 目录中

## 注意事项

1. 确保所有依赖都已正确安装
2. 如果遇到图标问题，确保 `app_icon.ico` 文件存在且格式正确
3. 如果遇到 PyQt5 相关错误，可能需要重新安装 PyQt5：
```bash
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5
```

## 测试安装包

1. 运行生成的安装包
2. 检查程序是否能正常启动
3. 测试所有功能是否正常工作
4. 验证卸载功能是否正常

## 常见问题

1. 如果程序无法启动，检查是否所有依赖都已正确打包
2. 如果出现 PyQt5 相关错误，尝试重新安装 PyQt5
3. 如果图标显示不正确，确保图标文件格式正确

## 发布说明

1. 版本号：0.1.0
2. 支持的操作系统：Windows 10/11
3. 最低系统要求：
   - Windows 10 或更高版本
   - 4GB RAM
   - 500MB 可用磁盘空间 