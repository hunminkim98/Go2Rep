@echo off
REM Go2Rep v2.0 환경 설정 스크립트 (Windows)

echo 🚀 Go2Rep v2.0 개발 환경 설정을 시작합니다...

REM Conda 설치 확인
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Conda가 설치되지 않았습니다. 먼저 Conda를 설치해주세요.
    echo    https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo ✅ Conda 확인됨

REM 기존 환경 확인
conda env list | findstr "Go2Rep" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  기존 Go2Rep 환경이 발견되었습니다.
    set /p choice="기존 환경을 삭제하고 재생성하시겠습니까? (y/N): "
    if /i "%choice%"=="y" (
        echo 🗑️  기존 환경 삭제 중...
        conda env remove -n Go2Rep -y
    ) else (
        echo 📝 기존 환경을 업데이트합니다...
        conda env update -f environment.yml
        echo ✅ 환경 업데이트 완료!
        pause
        exit /b 0
    )
)

REM 새 환경 생성
echo 🏗️  새 Conda 환경 생성 중...
conda env create -f environment.yml

REM 환경 활성화
echo 🔄 환경 활성화 중...
call conda activate Go2Rep

REM 설치 확인
echo 🔍 설치 확인 중...

REM Python 버전 확인
python --version

REM PySide6 확인
python -c "import PySide6; print('PySide6:', PySide6.__version__)" 2>nul
if %errorlevel% equ 0 (
    echo ✅ PySide6 설치 확인됨
) else (
    echo ❌ PySide6 설치 실패
    pause
    exit /b 1
)

REM FFmpeg 확인
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg 설치 확인됨
) else (
    echo ⚠️  FFmpeg가 설치되지 않았습니다. 비디오 처리 기능이 제한될 수 있습니다.
)

REM UI 임포트 테스트
python -c "from go2rep.ui.main_window import MainWindow; print('✅ UI 임포트 성공')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ UI 컴포넌트 임포트 성공
) else (
    echo ❌ UI 컴포넌트 임포트 실패
    pause
    exit /b 1
)

REM 테스트 실행
echo 🧪 기본 테스트 실행 중...
python -m pytest go2rep/tests/test_basic.py -v
if %errorlevel% equ 0 (
    echo ✅ 기본 테스트 통과
) else (
    echo ⚠️  일부 테스트가 실패했습니다. 개발을 계속 진행할 수 있습니다.
)

echo.
echo 🎉 Go2Rep v2.0 개발 환경 설정이 완료되었습니다!
echo.
echo 📋 다음 단계:
echo    1. conda activate Go2Rep
echo    2. python go2rep/main.py  # 애플리케이션 실행
echo    3. pytest go2rep/tests/ -v  # 전체 테스트 실행
echo.
echo 📚 자세한 내용은 SETUP.md를 참조하세요.
echo.
echo 🔧 개발 도구 설정 (선택사항):
echo    pre-commit install  # Git 훅 설정
echo    black go2rep/       # 코드 포맷팅
echo    ruff check go2rep/  # 린팅

pause
