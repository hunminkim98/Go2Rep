<!-- 1f5e551f-64da-4f7f-a5ac-0ab78b2aad2e 97c7a479-bd49-4767-a1e9-1e2293670776 -->
# GoPro Control 대시보드 구현 계획

## 개요

대시보드 중심형 디자인으로 GoPro 카메라 제어 페이지를 구현합니다. 6개의 mock 데이터를 사용하여 UI/UX를 검증하고, 실제 Backend API와 연동합니다.

## 구현 파일

### 1. ViewModel 생성

**파일**: `PerforMetrics/ViewModels/GoProControlViewModel.cs`

- ObservableCollection으로 GoProDevice 리스트 관리
- 6개의 mock 데이터 초기화 (다양한 연결 상태)
- ApiService를 통한 실제 API 호출 메서드
- ScanDevicesCommand: BLE/COHN 스캔
- StartRecordingCommand: 전체/선택 녹화 시작
- StopRecordingCommand: 전체/선택 녹화 중지
- ApplySettingsCommand: FPS/해상도 일괄 적용
- ToggleDeviceCommand: 개별 장치 녹화 토글
- 빠른 설정 프로퍼티: SelectedFps, SelectedResolution
- 로딩 상태 및 에러 처리

### 2. View XAML 생성

**파일**: `PerforMetrics/Views/GoProControlView.axaml`

- 3단 레이아웃 구조:

1. 상단 컨트롤 바 (56px 높이)

- 스캔, 전체 녹화, 전체 중지 버튼

2. 중앙 GoPro 카드 그리드 (ScrollViewer + WrapPanel)

- 반응형 레이아웃 (ItemsControl with WrapPanel)
- 각 카드: 이름, 상태 인디케이터, 연결 정보, 녹화/설정 버튼
- 카드 크기: 약 280x240px

3. 하단 빠른 설정 패널 (120px 높이)

- FPS 선택: 60/120/240 RadioButton
- 해상도 선택: 1080p/2.7K/4K RadioButton
- 전체 적용 버튼

색상 테마는 LandingPage와 동일하게 유지

### 3. View Code-behind 생성

**파일**: `PerforMetrics/Views/GoProControlView.axaml.cs`

- InitializeComponent 호출
- DataContext 설정

### 4. 네비게이션 연동

**파일**: `PerforMetrics/ViewModels/LandingPageViewModel.cs` (수정)

- NavigateToGoProControl 메서드에서 MainWindowViewModel에 뷰 전환 이벤트 발생
- EventHandler 추가로 MainWindow와 통신

**파일**: `PerforMetrics/ViewModels/MainWindowViewModel.cs` (수정)

- LandingPageViewModel의 네비게이션 이벤트 구독
- CurrentView를 GoProControlView로 변경하는 메서드 추가
- GoProControlViewModel 인스턴스 관리

### 5. Mock 데이터 상세

6개의 GoPro 장치:

1. GoPro 8577 - Connected (BLE)
2. GoPro 8579 - Connected (COHN, IP: 192.168.1.101)
3. GoPro 8580 - Ready (COHN, IP: 192.168.1.102)
4. GoPro 8581 - Ready (BLE)
5. GoPro 8582 - Connected (COHN, IP: 192.168.1.103)
6. GoPro 8583 - Disconnected

## 구현 순서

1. GoProControlViewModel 생성 및 mock 데이터 구현
2. GoProControlView XAML 레이아웃 구현
3. GoProControlView code-behind 구현
4. MainWindowViewModel 네비게이션 로직 추가
5. LandingPageViewModel 네비게이션 이벤트 연결
6. API 호출 로직 통합 및 테스트

## 주요 기능

- 반응형 카드 그리드 (창 크기에 따라 열 개수 자동 조정)
- 실시간 연결 상태 표시 (색상 인디케이터)
- 개별/일괄 제어 지원
- Backend API 실제 호출 (ScanGoProDevicesAsync, ControlRecordingAsync, ChangeSettingsAsync)
- 에러 핸들링 및 사용자 피드백

### To-dos

- [ ] GoProControlViewModel.cs 생성 - mock 데이터 6개, API 호출 메서드, 커맨드 구현
- [ ] GoProControlView.axaml 생성 - 3단 레이아웃(상단 바, 카드 그리드, 하단 설정)
- [ ] GoProControlView.axaml.cs 생성 - InitializeComponent 및 DataContext 설정
- [ ] MainWindowViewModel.cs 수정 - GoProControlView로 전환하는 네비게이션 로직 추가
- [ ] LandingPageViewModel.cs 수정 - NavigateToGoProControl에서 MainWindow로 이벤트 전달
- [ ] 네비게이션 및 mock 데이터 표시 테스트