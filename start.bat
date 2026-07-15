@echo off
chcp 65001 >nul 2>&1
title Desktop Battle - 桌面火柴人大乱斗

echo ╔══════════════════════════════════════════╗
echo ║    Desktop Battle - 桌面火柴人大乱斗      ║
echo ╚══════════════════════════════════════════╝
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
python -c "import numpy; import pymunk; import py_trees; import loguru; import pydantic; import httpx" >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 正在安装依赖，请稍候...
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [安装] 依赖安装完成
) else (
    echo [OK] 依赖已就绪
)

echo [2/3] 初始化...
if not exist "logs" mkdir logs
if not exist "logs\system" mkdir logs\system
if not exist "logs\behavior" mkdir logs\behavior
if not exist "logs\error" mkdir logs\error
if not exist "logs\strategy" mkdir logs\strategy

echo [3/3] 启动游戏...
echo.
echo 提示: 右键点击托盘图标可以暂停/打开面板/退出
echo.
python -m src.main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 游戏异常退出，请查看 logs\error\ 目录下的日志
    pause
)
