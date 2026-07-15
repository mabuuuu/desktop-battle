@echo off
title Desktop Battle

cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import numpy; import pymunk; import py_trees; import loguru; import pydantic; import httpx" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INSTALL] Installing dependencies...
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [INSTALL] Done
) else (
    echo [OK] Dependencies ready
)

echo [2/3] Initializing...
if not exist "logs" mkdir logs
if not exist "logs\system" mkdir logs\system
if not exist "logs\behavior" mkdir logs\behavior
if not exist "logs\error" mkdir logs\error
if not exist "logs\strategy" mkdir logs\strategy

echo [3/3] Starting game...
echo.
echo Tip: Right-click tray icon to pause / open panel / exit
echo.
python -m src.main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Game exited abnormally. Check logs\error\ for details
    pause
)