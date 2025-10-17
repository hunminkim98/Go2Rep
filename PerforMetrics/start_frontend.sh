#!/bin/bash

# PerforMetrics Frontend Startup Script
# This script starts the Avalonia desktop application

echo "Starting PerforMetrics Frontend..."

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "Error: .NET SDK is not installed"
    echo "Please install .NET 9.0 or later from https://dotnet.microsoft.com/download"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build and run the application
echo "Building and running PerforMetrics..."
dotnet run

