@echo off
echo =====================================
echo Canvas下载助手 - Windows打包脚本
echo =====================================
echo.

echo 检查Python安装...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python未安装或未添加到PATH！请安装Python 3.8或更高版本。
    pause
    exit /b 1
)

echo.
echo 安装依赖...
pip install -U pip
pip install -U canvassyncer PyQt5 pyinstaller pillow
if %ERRORLEVEL% NEQ 0 (
    echo 安装依赖失败！
    pause
    exit /b 1
)

echo.
echo 生成图标...
python create_icon.py
if %ERRORLEVEL% NEQ 0 (
    echo 图标创建失败！继续使用默认图标...
)

echo.
echo 开始打包应用程序...
pyinstaller canvas_downloader_win.spec
if %ERRORLEVEL% NEQ 0 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo 打包成功！可执行文件位于dist目录。
echo.
echo 是否创建安装包？(Y/N)
set /p CREATE_INSTALLER=

if /i "%CREATE_INSTALLER%"=="Y" (
    echo.
    echo 检查Inno Setup安装...
    where iscc >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo 未找到Inno Setup！请安装Inno Setup并将其添加到PATH。
        echo 您可以从这里下载: https://jrsoftware.org/isdl.php
        echo 安装后请手动运行: iscc setup.iss
    ) else (
        echo 创建安装包...
        iscc setup.iss
        if %ERRORLEVEL% NEQ 0 (
            echo 创建安装包失败！
        ) else (
            echo 安装包创建成功！位于installer目录。
        )
    )
)

echo.
echo 完成！
pause 