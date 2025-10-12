# Go2Rep v2.0 개발 환경 설정 가이드

## Conda 환경 생성 및 설정

### 1. Conda 환경 생성

```bash
# 방법 1: environment.yml 사용 (권장)
conda env create -f environment.yml

# 방법 2: 수동 생성
conda create -n Go2Rep python=3.10
conda activate Go2Rep
```

### 2. 환경 활성화

```bash
conda activate Go2Rep
```

### 3. 의존성 설치 확인

```bash
# Conda 패키지 확인
conda list

# PySide6 설치 확인
python -c "import PySide6; print('PySide6 version:', PySide6.__version__)"

# UI 임포트 테스트
python -c "from go2rep.ui.main_window import MainWindow; print('✅ UI import successful')"
```

## 개발 도구 설정

### 1. Pre-commit 훅 설정 (선택사항)

```bash
# Pre-commit 설치 및 설정
pre-commit install

# 수동 실행
pre-commit run --all-files
```

### 2. 코드 포맷팅

```bash
# Black으로 코드 포맷팅
black go2rep/

# Ruff로 린팅
ruff check go2rep/
ruff format go2rep/
```

### 3. 타입 체킹

```bash
# MyPy로 타입 체킹
mypy go2rep/
```

## 테스트 실행

### 1. 단위 테스트

```bash
# 모든 테스트 실행
pytest go2rep/tests/ -v

# 특정 테스트 실행
pytest go2rep/tests/unit/test_camera.py -v

# 커버리지 포함
pytest go2rep/tests/ --cov=go2rep --cov-report=html
```

### 2. UI 테스트

```bash
# Qt 테스트 실행
pytest go2rep/tests/ui/ -v
```

## 애플리케이션 실행

### 1. 기본 실행

```bash
# 메인 애플리케이션 실행
python go2rep/main.py
```

### 2. 개발 모드 실행

```bash
# 디버그 모드로 실행
python -X dev go2rep/main.py
```

## 문제 해결

### 1. PySide6 설치 문제

```bash
# PySide6 재설치
pip uninstall PySide6 PySide6-Addons
pip install PySide6>=6.6.0 PySide6-Addons>=6.6.0

# 또는 conda로 설치
conda install -c conda-forge pyside6
```

### 2. FFmpeg 문제

```bash
# FFmpeg 설치 확인
ffmpeg -version

# Conda로 FFmpeg 설치
conda install -c conda-forge ffmpeg
```

### 3. CUDA/GPU 문제

```bash
# CUDA 버전 확인
nvidia-smi

# ONNX Runtime GPU 버전 설치
pip install onnxruntime-gpu>=1.16.0
```

### 4. BLE (Bluetooth) 문제

```bash
# Bleak 설치 확인
python -c "import bleak; print('Bleak version:', bleak.__version__)"

# macOS에서 Bluetooth 권한 확인
# 시스템 환경설정 > 보안 및 개인 정보 보호 > 개인 정보 보호 > Bluetooth
```

## 환경 변수 설정

### 1. 개발용 환경 변수

```bash
# .env 파일 생성 (선택사항)
echo "GO2REP_DEBUG=1" > .env
echo "GO2REP_LOG_LEVEL=DEBUG" >> .env
```

### 2. GoPro 인증서 경로

```bash
# 인증서 경로 설정
export GOPRO_CERT_PATH="/path/to/certifications/"
```

## 프로젝트 구조

```
Go2Rep/
├── go2rep/                 # 메인 패키지
│   ├── core/              # 비즈니스 로직
│   ├── ui/                # UI 컴포넌트
│   ├── utils/             # 유틸리티
│   └── tests/             # 테스트
├── tools/                 # 기존 도구 (레거시)
├── calib/                 # 캘리브레이션 데이터
├── certifications/        # GoPro 인증서
├── Assets/               # UI 자산
├── requirements.txt       # pip 의존성
├── environment.yml       # conda 환경
└── SETUP.md             # 이 파일
```

## 추가 리소스

- [PySide6 공식 문서](https://doc.qt.io/qtforpython/)
- [Conda 환경 관리](https://docs.conda.io/en/latest/)
- [Pytest 문서](https://docs.pytest.org/)
- [Black 코드 포맷터](https://black.readthedocs.io/)
- [Ruff 린터](https://docs.astral.sh/ruff/)

## 지원

문제가 발생하면 다음을 확인하세요:

1. Python 버전이 3.10인지 확인
2. Conda 환경이 올바르게 활성화되었는지 확인
3. 모든 의존성이 설치되었는지 확인
4. 시스템 요구사항을 충족하는지 확인

```bash
# 시스템 정보 확인
python --version
conda --version
pip --version
```
