@echo off
REM PerforMetrics Full Stack Launcher for Windows
REM This batch file calls the Python launcher script

echo Starting PerforMetrics Full Stack...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or later
    pause
    exit /b 1
)

REM Run the Python launcher
python "%~dp0start_fullstack.py"

if %errorlevel% neq 0 (
    echo.
    echo An error occurred while running PerforMetrics
    pause
)

