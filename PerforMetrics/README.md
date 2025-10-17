# PerforMetrics

Modern desktop application for multi-camera GoPro control and motion analysis, built with Avalonia UI (C#) and FastAPI (Python).

## Overview

PerforMetrics provides a unified interface for:
- **GoPro Control**: Multi-camera control via BLE, WiFi AP, and COHN protocols
- **Synchronization**: Manual and timecode-based video synchronization
- **Classification**: Theia-compatible video processing
- **Calibration**: Camera intrinsic and extrinsic calibration
- **Motion Analysis**: Markerless 3D motion capture
- **Report Generation**: Biomechanical metrics extraction and visualization

## Architecture

- **Frontend**: Avalonia UI (C# .NET 9.0) - Cross-platform desktop application
- **Backend**: FastAPI (Python 3.8+) - REST API server
- **Communication**: HTTP REST API with JSON

## Prerequisites

### For Frontend (C# Avalonia)
- .NET 9.0 SDK or later
- macOS 10.15+ or Windows 10+

### For Backend (Python)
- Python 3.8 or later
- pip (Python package manager)

## Installation

### 1. Clone or Navigate to the Project

```bash
cd /Users/a/Desktop/Go2Rep/PerforMetrics
```

### 2. Backend Setup

```bash
cd Backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

The frontend is already set up. Just ensure .NET 9.0 is installed:

```bash
dotnet --version
```

## Running the Application

### Option 1: 통합 실행 (가장 권장)

**한 번의 명령으로 전체 스택 실행 (백엔드 + 프론트엔드)**

이 방법은 자동으로:
- Anaconda 환경 확인 및 활성화 (Go2Rep)
- Python 의존성 설치
- .NET SDK 확인
- 백엔드 서버 시작
- 프론트엔드 앱 시작

```bash
# macOS/Linux
python3 start_fullstack.py

# 또는
./start_fullstack.py

# Windows
python start_fullstack.py

# 또는
start_fullstack.bat
```

**참고**: 이 스크립트는 Anaconda의 `Go2Rep` 환경을 사용합니다. 환경이 없으면 자동으로 생성을 제안합니다.

### Option 2: 개별 실행 스크립트

#### Start Backend (Terminal 1)
```bash
# macOS/Linux
./Backend/start_backend.sh

# Windows
Backend\start_backend.bat
```

The backend will start on `http://localhost:8000`

#### Start Frontend (Terminal 2)
```bash
# macOS/Linux
./start_frontend.sh

# Windows
start_frontend.bat
```

### Option 3: 수동 실행

#### Start Backend
```bash
cd Backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

#### Start Frontend
```bash
dotnet run
```

## Project Structure

```
PerforMetrics/
├── Backend/                        # Python FastAPI Backend
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration settings
│   ├── requirements.txt           # Python dependencies
│   ├── routers/                   # API route handlers
│   │   ├── gopro_ble.py          # BLE control endpoints
│   │   └── gopro_cohn.py         # COHN control endpoints
│   └── start_backend.sh/bat      # Backend startup scripts
├── Models/                        # Data models
│   └── GoProDevice.cs
├── Services/                      # Business logic services
│   └── ApiService.cs             # Backend API client
├── ViewModels/                    # MVVM ViewModels
│   ├── ViewModelBase.cs
│   ├── MainWindowViewModel.cs
│   └── LandingPageViewModel.cs
├── Views/                         # UI Views
│   ├── MainWindow.axaml
│   ├── MainWindow.axaml.cs
│   ├── LandingPage.axaml
│   └── LandingPage.axaml.cs
├── Converters/                    # Value converters
│   ├── StatusColorConverter.cs
│   └── StatusTextColorConverter.cs
├── Assets/                        # Images and resources
├── App.axaml                      # Application definition
├── App.axaml.cs
├── Program.cs                     # Application entry point
├── ViewLocator.cs                 # MVVM view locator
├── PerforMetrics.csproj          # C# project file
├── appsettings.json              # Application settings
├── start_fullstack.py            # Unified launcher (RECOMMENDED)
├── start_fullstack.bat           # Windows launcher wrapper
├── start_frontend.sh/bat         # Frontend startup scripts
├── README.md                      # This file
├── QUICKSTART.md                 # Quick start guide
├── LAUNCHER_GUIDE.md             # Detailed launcher guide
└── PROJECT_SUMMARY.md            # Project summary
```

## Features

### Landing Page

The landing page provides quick access to all major features:

1. **GoPro Control** - Camera discovery, connection, recording control
2. **Synchronization** - Video synchronization tools
3. **Classification** - Video processing for Theia
4. **Calibration** - Camera calibration workflows
5. **Motion Analysis** - 3D pose estimation
6. **Report Generator** - Biomechanical analysis and reporting

### Backend Status Indicator

The status bar at the bottom shows:
- Backend connection status (Connected/Disconnected)
- Version information

## API Endpoints

### Health Check
- `GET /health` - Backend health status
- `GET /` - API information
- `GET /api/system/info` - System information

### GoPro BLE Control
- `GET /api/gopro/ble/scan` - Scan for GoPro cameras
- `POST /api/gopro/ble/connect/{identifier}` - Connect to camera
- `POST /api/gopro/ble/recording` - Control recording
- `POST /api/gopro/ble/settings` - Change camera settings
- `POST /api/gopro/ble/power-off/{identifier}` - Power off camera

### GoPro COHN Control
- `POST /api/gopro/cohn/establish-connection/{identifier}` - Setup COHN
- `GET /api/gopro/cohn/devices` - List COHN devices
- `POST /api/gopro/cohn/recording` - Control recording
- `POST /api/gopro/cohn/settings` - Change settings
- `POST /api/gopro/cohn/download` - Download videos
- `GET /api/gopro/cohn/certificate-status/{identifier}` - Check certificate

## Development

### Building the Frontend

```bash
dotnet build
```

### Running in Development Mode

```bash
dotnet run
```

### API Documentation

When the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Technology Stack

### Frontend
- **Avalonia UI 11.3.6** - Cross-platform XAML-based UI framework
- **CommunityToolkit.Mvvm** - MVVM helpers and commands
- **System.Net.Http.Json** - HTTP client with JSON support
- **ReactiveUI** - Reactive programming for UI

### Backend
- **FastAPI 0.115.0** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Bleak** - Bluetooth Low Energy library
- **Requests** - HTTP library

## Troubleshooting

### Backend Won't Start

1. Check Python version: `python3 --version`
2. Ensure virtual environment is activated
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check if port 8000 is available

### Frontend Won't Start

1. Check .NET version: `dotnet --version`
2. Clean and rebuild: `dotnet clean && dotnet build`
3. Check for compilation errors

### Backend Connection Failed

1. Ensure backend is running on `http://localhost:8000`
2. Check firewall settings
3. Verify backend health: `curl http://localhost:8000/health`

## Future Enhancements

- Complete implementation of GoPro control functions
- Add navigation between pages
- Implement remaining feature pages
- Add real-time video preview
- Enhanced error handling and logging
- User preferences and settings
- Dark mode support

## License

Part of the Go2Rep project.

## Credits

Original project: [Go2Rep](https://github.com/ShabahangShayegan/Go2Rep)

