# GoPro Control Scripts

GoPro HERO 카메라 (11/13 모델 테스트 완료)를 제어하기 위한 독립 실행형 Python 스크립트 모음입니다.

## 개요

이 프로젝트는 GoPro 카메라를 프로그래밍 방식으로 제어할 수 있는 스크립트들을 제공합니다:
- BLE(Bluetooth Low Energy)를 통한 GoPro 11 및 이전 모델 제어
- WiFi AP를 통한 비디오 다운로드 (GoPro 11 및 이전 모델)
- COHN(Camera over Home Network)을 통한 GoPro 13/12 제어
- 라이브 프리뷰 스트리밍

## 설치

### 사전 요구사항

- Python 3.8 이상
- Bluetooth 지원 (BLE 기능 사용 시)
- WiFi 지원

### 의존성 설치

```bash
pip install -r requirements.txt
```

## 폴더 구조

```
GoPro/
├── README.md                    # 이 파일
├── requirements.txt             # Python 의존성
├── BLE/                         # BLE 관련 기능 (GoPro 11 및 이전 모델)
│   ├── scan_gopros.py          # GoPro 카메라 스캔
│   ├── start_recording.py      # 녹화 시작/중지
│   ├── power_off.py            # 전원 끄기
│   └── change_settings.py      # FPS/해상도 설정 변경
├── WiFi_AP/                     # WiFi AP 관련 기능 (GoPro 11 및 이전 모델)
│   └── download_videos.py      # 비디오 다운로드
├── COHN/                        # COHN 관련 기능 (GoPro 13/12)
│   ├── establish_connection.py # WiFi 연결 설정 및 인증서 생성
│   ├── start_recording.py      # 녹화 시작/중지
│   ├── change_settings.py      # 설정 변경
│   └── download_videos.py      # 비디오 다운로드
├── LiveStreaming/
│   └── preview_stream.py       # 라이브 프리뷰
└── certifications/              # COHN 인증서 저장 폴더
    └── .gitkeep
```

## 사용법

### BLE 기능 (GoPro 11 및 이전 모델)

#### 1. GoPro 카메라 스캔
```bash
python BLE/scan_gopros.py
```

#### 2. 녹화 시작/중지
```bash
python BLE/start_recording.py
```
- 모든 GoPro를 검색하고 연결
- Enter 키를 눌러 녹화 중지

#### 3. 전원 끄기
```bash
python BLE/power_off.py --identifier <last_4_digits>
```

#### 4. 설정 변경 (FPS/해상도)
```bash
python BLE/change_settings.py --fps 120 --resolution 2700
```
- FPS: 60, 120, 240
- Resolution: 1080, 2700 (2.7K), 4000 (4K)

### WiFi AP 기능 (GoPro 11 및 이전 모델)

#### 비디오 다운로드
```bash
python WiFi_AP/download_videos.py --output ./my_videos
```
- BLE로 연결 후 WiFi AP 활성화
- 날짜별 비디오 선택 및 다운로드

### COHN 기능 (GoPro 13/12)

**중요**: COHN 기능을 사용하려면 먼저 인증서를 생성해야 합니다.

#### 1. WiFi 연결 설정 및 인증서 생성
```bash
python COHN/establish_connection.py
```
- GoPro와 BLE로 연결
- WiFi 네트워크에 프로비저닝
- 인증서를 `certifications/` 폴더에 저장

#### 2. 녹화 시작/중지
```bash
python COHN/start_recording.py
```
- Spacebar를 눌러 모든 GoPro 녹화 중지

#### 3. 설정 변경
```bash
python COHN/change_settings.py
```

#### 4. 비디오 다운로드
```bash
python COHN/download_videos.py
```
- HTTPS를 통한 암호화된 다운로드
- 날짜 및 시간 범위 선택 가능

### 라이브 스트리밍

#### 프리뷰 스트림
```bash
python LiveStreaming/preview_stream.py --identifier <last_4_digits>
```

## GoPro 11 vs GoPro 13/12 차이점

| 기능 | GoPro 11 및 이전 모델 | GoPro 13/12 |
|------|----------------------|-------------|
| **프로토콜** | BLE + WiFi AP | HTTPS via COHN |
| **인증서 필요** | 아니오 | 예 (필수) |
| **프리뷰** | WiFi AP 지원 | COHN 지원* |
| **미디어 다운로드** | BLE + WiFi 기본 | HTTPS 암호화 |

\* 현재 구현되지 않음

## 문제 해결

### BLE 연결 실패
- Bluetooth가 활성화되어 있는지 확인
- GoPro가 페어링 모드인지 확인
- 다른 기기와의 연결을 끊고 재시도

### WiFi 연결 실패
- GoPro WiFi AP가 활성화되었는지 확인
- 수동으로 GoPro WiFi 네트워크에 연결 시도
- 네트워크 설정 확인

### COHN 인증서 오류
- `establish_connection.py`를 먼저 실행했는지 확인
- `certifications/` 폴더에 인증서 파일이 있는지 확인
- 인증서를 삭제하고 재생성

## 참고 자료

- [GoPro Open Source](https://gopro.github.io/OpenGoPro/)
- [GoPro Labs - Precision Time Control](https://gopro.github.io/labs/control/precisiontime/)
- [GoPro Labs - Settings Control](https://gopro.github.io/labs/control/settings/)
- [Media Browser (WiFi-AP)](http://10.5.5.9/videos/DCIM/100GOPRO/)

## 라이센스

이 프로젝트는 원본 Go2Rep 프로젝트의 일부입니다.

## 기여

원본 프로젝트: [Go2Rep](https://github.com/ShabahangShayegan/Go2Rep)

