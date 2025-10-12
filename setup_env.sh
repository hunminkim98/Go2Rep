#!/bin/bash
# Go2Rep v2.0 환경 설정 스크립트

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 Go2Rep v2.0 개발 환경 설정을 시작합니다..."

# Conda 설치 확인
if ! command -v conda &> /dev/null; then
    echo "❌ Conda가 설치되지 않았습니다. 먼저 Conda를 설치해주세요."
    echo "   https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda 확인됨: $(conda --version)"

# 기존 환경 확인
if conda env list | grep -q "Go2Rep"; then
    echo "⚠️  기존 Go2Rep 환경이 발견되었습니다."
    read -p "기존 환경을 삭제하고 재생성하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  기존 환경 삭제 중..."
        conda env remove -n Go2Rep -y
    else
        echo "📝 기존 환경을 업데이트합니다..."
        conda env update -f environment.yml
        echo "✅ 환경 업데이트 완료!"
        exit 0
    fi
fi

# 새 환경 생성
echo "🏗️  새 Conda 환경 생성 중..."
conda env create -f environment.yml

# 환경 활성화
echo "🔄 환경 활성화 중..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate Go2Rep

# 설치 확인
echo "🔍 설치 확인 중..."

# Python 버전 확인
echo "Python 버전: $(python --version)"

# PySide6 확인
if python -c "import PySide6; print('PySide6:', PySide6.__version__)" 2>/dev/null; then
    echo "✅ PySide6 설치 확인됨"
else
    echo "❌ PySide6 설치 실패"
    exit 1
fi

# FFmpeg 확인
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg 설치 확인됨"
else
    echo "⚠️  FFmpeg가 설치되지 않았습니다. 비디오 처리 기능이 제한될 수 있습니다."
fi

# UI 임포트 테스트
if python -c "from go2rep.ui.main_window import MainWindow; print('✅ UI 임포트 성공')" 2>/dev/null; then
    echo "✅ UI 컴포넌트 임포트 성공"
else
    echo "❌ UI 컴포넌트 임포트 실패"
    exit 1
fi

# 테스트 실행
echo "🧪 기본 테스트 실행 중..."
if python -m pytest go2rep/tests/test_basic.py -v; then
    echo "✅ 기본 테스트 통과"
else
    echo "⚠️  일부 테스트가 실패했습니다. 개발을 계속 진행할 수 있습니다."
fi

echo ""
echo "🎉 Go2Rep v2.0 개발 환경 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "   1. conda activate Go2Rep"
echo "   2. python go2rep/main.py  # 애플리케이션 실행"
echo "   3. pytest go2rep/tests/ -v  # 전체 테스트 실행"
echo ""
echo "📚 자세한 내용은 SETUP.md를 참조하세요."
echo ""
echo "🔧 개발 도구 설정 (선택사항):"
echo "   pre-commit install  # Git 훅 설정"
echo "   black go2rep/       # 코드 포맷팅"
echo "   ruff check go2rep/  # 린팅"
