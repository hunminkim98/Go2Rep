@echo off
REM PerforMetrics Frontend Startup Script for Windows
REM This script starts the Avalonia desktop application

echo Starting PerforMetrics Frontend...

REM Check if .NET is installed
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: .NET SDK is not installed
    echo Please install .NET 9.0 or later from https://dotnet.microsoft.com/download
    exit /b 1
)

REM Get the directory of this script
cd /d "%~dp0"

REM Build and run the application
echo Building and running PerforMetrics...
dotnet run

pause

