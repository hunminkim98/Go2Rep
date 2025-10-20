#!/usr/bin/env python3
"""
PerforMetrics Full Stack Launcher
통합 실행 스크립트 - 백엔드와 프론트엔드를 한 번에 시작합니다
"""

import os
import sys
import platform
import subprocess
import time
import shutil
from pathlib import Path


class Colors:
    """터미널 색상 코드"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    """헤더 메시지 출력"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    """성공 메시지 출력"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message):
    """정보 메시지 출력"""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")


def print_warning(message):
    """경고 메시지 출력"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message):
    """에러 메시지 출력"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def get_os_type():
    """운영체제 타입 반환"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def find_conda():
    """Conda 실행 파일 경로 찾기"""
    os_type = get_os_type()
    
    # conda 명령어가 PATH에 있는지 확인
    conda_cmd = shutil.which("conda")
    if conda_cmd:
        return conda_cmd
    
    # 일반적인 Anaconda 설치 경로 확인
    if os_type == "windows":
        possible_paths = [
            os.path.expanduser("~/Anaconda3/Scripts/conda.exe"),
            os.path.expanduser("~/Miniconda3/Scripts/conda.exe"),
            "C:/ProgramData/anaconda3/Scripts/conda.exe",
            "C:/ProgramData/miniconda3/Scripts/conda.exe",
        ]
    else:  # macOS, Linux
        possible_paths = [
            os.path.expanduser("~/anaconda3/bin/conda"),
            os.path.expanduser("~/miniconda3/bin/conda"),
            os.path.expanduser("~/opt/anaconda3/bin/conda"),
            os.path.expanduser("~/opt/miniconda3/bin/conda"),
            "/opt/anaconda3/bin/conda",
            "/opt/miniconda3/bin/conda",
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def check_conda_env(conda_path, env_name="Go2Rep"):
    """Conda 환경이 존재하는지 확인"""
    try:
        result = subprocess.run(
            [conda_path, "env", "list"],
            capture_output=True,
            text=True,
            shell=False
        )
        return env_name in result.stdout
    except Exception as e:
        print_error(f"Conda 환경 확인 실패: {e}")
        return False


def create_conda_env(conda_path, env_name="Go2Rep"):
    """Conda 환경 생성"""
    print_info(f"'{env_name}' Conda 환경 생성중...")
    try:
        subprocess.run(
            [conda_path, "create", "-n", env_name, "python=3.10", "-y"],
            check=True
        )
        print_success(f"'{env_name}' 환경 생성완료")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"환경 생성 실패함: {e}")
        return False


def get_conda_python(conda_path, env_name="Go2Rep"):
    """Conda 환경의 Python 경로 가져오기"""
    os_type = get_os_type()
    
    try:
        # conda info 명령으로 환경 경로 확인
        result = subprocess.run(
            [conda_path, "env", "list"],
            capture_output=True,
            text=True,
            shell=False
        )
        
        # 환경 경로 파싱
        for line in result.stdout.split('\n'):
            if env_name in line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    env_path = parts[-1]
                    if os_type == "windows":
                        python_path = os.path.join(env_path, "python.exe")
                    else:
                        python_path = os.path.join(env_path, "bin", "python")
                    
                    if os.path.exists(python_path):
                        return python_path
    except Exception as e:
        print_warning(f"Conda Python 경로 찾기 실패: {e}")
    
    return None


def install_backend_dependencies(python_path, backend_dir):
    """백엔드 의존성 설치"""
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"requirements.txt를 찾을 수 없습니다: {requirements_file}")
        return False
    
    print_info("백엔드 Python 의존성 설치중...")
    try:
        subprocess.run(
            [python_path, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            cwd=str(backend_dir)
        )
        print_success("백엔드 의존성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"의존성 설치 실패: {e}")
        return False


def check_dotnet():
    """dotnet SDK 설치 확인"""
    try:
        result = subprocess.run(
            ["dotnet", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print_success(f".NET SDK 발견: v{version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error(".NET SDK가 설치되어 있지 않습니다")
        print_info("https://dotnet.microsoft.com/download 에서 .NET 9.0 이상을 설치하세요")
        return False


def start_backend(python_path, backend_dir):
    """백엔드 서버 시작"""
    print_info("백엔드 서버를 시작하는 중...")
    
    main_py = backend_dir / "main.py"
    if not main_py.exists():
        print_error(f"main.py를 찾을 수 없습니다: {main_py}")
        return None
    
    try:
        os_type = get_os_type()
        
        if os_type == "windows":
            # Windows에서는 CREATE_NEW_CONSOLE 플래그 사용
            process = subprocess.Popen(
                [python_path, str(main_py)],
                cwd=str(backend_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os_type == "windows" else 0,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # macOS/Linux에서는 nohup 사용
            process = subprocess.Popen(
                [python_path, str(main_py)],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
        
        # 백엔드 시작 대기
        print_info("백엔드 시작을 기다리는 중... (5초)")
        time.sleep(5)
        
        # 프로세스가 살아있는지 확인
        if process.poll() is None:
            print_success("백엔드 서버가 시작되었습니다 (http://localhost:8000)")
            return process
        else:
            print_error("백엔드 서버 시작 실패")
            return None
            
    except Exception as e:
        print_error(f"백엔드 시작 중 오류: {e}")
        return None


def start_frontend(frontend_dir):
    """프론트엔드 앱 시작"""
    print_info("프론트엔드 애플리케이션을 시작하는 중...")
    
    csproj = frontend_dir / "PerforMetrics.csproj"
    if not csproj.exists():
        print_error(f"PerforMetrics.csproj를 찾을 수 없습니다: {csproj}")
        return None
    
    try:
        # dotnet run을 포그라운드에서 실행
        print_success("프론트엔드를 시작합니다...")
        process = subprocess.Popen(
            ["dotnet", "run"],
            cwd=str(frontend_dir)
        )
        return process
        
    except Exception as e:
        print_error(f"프론트엔드 시작 중 오류: {e}")
        return None


def main():
    """메인 함수"""
    print_header("PerforMetrics Full Stack Launcher")
    
    # 현재 디렉토리 확인
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir / "Backend"
    
    print_info(f"작업 디렉토리: {script_dir}")
    print_info(f"운영체제: {get_os_type().upper()}")
    
    # 1. Conda 확인
    print_header("1. Conda 환경 확인")
    conda_path = find_conda()
    
    if not conda_path:
        print_error("Anaconda 또는 Miniconda를 찾을 수 없습니다")
        print_info("https://www.anaconda.com/download 에서 설치하세요")
        sys.exit(1)
    
    print_success(f"Conda 발견: {conda_path}")
    
    # 2. Go2Rep 환경 확인
    print_header("2. Go2Rep 환경 확인")
    env_name = "Go2Rep"
    
    if not check_conda_env(conda_path, env_name):
        print_warning(f"'{env_name}' 환경 존재하지 않음")
        response = input(f"'{env_name}' 환경을 생성하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            if not create_conda_env(conda_path, env_name):
                sys.exit(1)
        else:
            print_error("환경이 필요합니다. 종료합니다.")
            sys.exit(1)
    else:
        print_success(f"'{env_name}' 환경 존재함")
    
    # 3. Python 경로 가져오기
    python_path = get_conda_python(conda_path, env_name)
    if not python_path:
        print_error("Conda 환경의 Python 찾을 수 없음")
        sys.exit(1)
    
    print_success(f"Python 경로: {python_path}")
    
    # 4. 백엔드 의존성 설치
    print_header("3. 백엔드 의존성 설치")
    if not install_backend_dependencies(python_path, backend_dir):
        print_warning("의존성 설치 실패함. 계속 진행중...")
    
    # 5. .NET SDK 확인
    print_header("4. .NET SDK 확인")
    if not check_dotnet():
        sys.exit(1)
    
    # 6. 백엔드 시작
    print_header("5. 백엔드 서버 시작")
    backend_process = start_backend(python_path, backend_dir)
    
    if not backend_process:
        print_error("백엔드 시작 실패")
        sys.exit(1)
    
    # 7. 프론트엔드 시작
    print_header("6. 프론트엔드 애플리케이션 시작")
    frontend_process = start_frontend(script_dir)
    
    if not frontend_process:
        print_error("프론트엔드 시작 실패")
        if backend_process:
            backend_process.terminate()
        sys.exit(1)
    
    # 8. 완료 메시지
    print_header("PerforMetrics 실행 중")
    print_success("백엔드: http://localhost:8000")
    print_success("프론트엔드: 애플리케이션 창")
    # print_info("\n프로그램을 종료하려면 Ctrl+C를 누르세요\n")
    
    try:
        # 프론트엔드가 종료될 때까지 대기
        frontend_process.wait()
    except KeyboardInterrupt:
        print_info("\n종료 중...")
    finally:
        # 프로세스 정리
        if frontend_process and frontend_process.poll() is None:
            print_info("프론트엔드를 종료하는 중...")
            frontend_process.terminate()
            
        if backend_process and backend_process.poll() is None:
            print_info("백엔드를 종료하는 중...")
            backend_process.terminate()
        
        print_success("PerforMetrics가 종료되었습니다")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

