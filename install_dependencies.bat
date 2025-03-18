@echo off
echo 正在安装Python依赖...

REM 检查Python是否在PATH中
python --version >nul 2>&1
if errorlevel 1 (
    echo Python未找到，请确保Python已正确安装并添加到PATH中
    pause
    exit /b 1
)

REM 升级pip
python -m pip install --upgrade pip

REM 安装必要的依赖
echo 正在安装canvassyncer...
python -m pip install canvassyncer

echo 正在安装PyQt5...
python -m pip install PyQt5

echo 依赖安装完成！
pause 