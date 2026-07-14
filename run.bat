@echo off
title Internet Analyzer
color 0F
cls

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Starting Internet Analyzer...
echo.
python "%~dp0internet_analyzer.py"
pause
