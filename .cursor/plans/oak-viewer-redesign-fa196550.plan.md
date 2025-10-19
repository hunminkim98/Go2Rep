<!-- fa196550-a3fb-4d98-9a5d-c3c5cce92b49 f3f17376-782b-41b5-b8d6-08b0aad5a1c0 -->
# 전문가스러운 시작 애니메이션 추가

## 개요

앱 시작 시 로고 페이드 인, 로딩 인디케이터, 부드러운 화면 전환 효과를 구현하여 전문적인 첫인상을 제공하옵니다.

## 디자인 사양 (사용자 선택 반영)

- **배경**: 흰색 (#FFFFFF)
- **브랜드 컬러**: 파란색 (#3B82F6)
- **로고**: Shield 아이콘 + "PerforMetrics" 텍스트 (현재 사용 중)
- **로딩**: 원형 ProgressRing (Avalonia 기본, 회전 애니메이션)
- **버전**: 하단에 "v1.0.0" 표시
- **타이밍**: 3-4초 (여유 있는 전환)
- **Backend**: Health check 수행하되 실패 시에도 계속 진행

## 애니메이션 시퀀스 (총 3.5초)

1. **0.0s - 1.0s**: 로고 페이드 인 + 위에서 아래로 부드럽게 이동
2. **0.5s - 1.0s**: 버전 정보 페이드 인 (로고와 동시)
3. **1.0s - 3.0s**: ProgressRing 회전 애니메이션 (로딩 중)
4. **3.0s - 3.6s**: CrossFade로 메인 화면 전환

## 구현할 파일

### 1. Views/SplashScreen.axaml (새 파일)

```xml
- Grid 레이아웃 (중앙 정렬)
- StackPanel:
  - PathIcon (Shield, 48x48)
  - TextBlock "PerforMetrics" (FontSize 32, Bold)
- ProgressRing (하단, 32x32, IsIndeterminate=True)
- TextBlock "v1.0.0" (최하단, 작은 글씨)
- 로고 페이드 인 애니메이션
- 버전 페이드 인 애니메이션 (지연)
```

### 2. Views/SplashScreen.axaml.cs (새 파일)

```csharp
- UserControl 상속
- 생성자에서 애니메이션 자동 시작
```

### 3. ViewModels/SplashScreenViewModel.cs (새 파일)

```csharp
- IsLoading 속성
- VersionInfo 속성 ("v1.0.0")
- StartLoadingAsync() 메서드:
  - Backend health check 수행
  - 최소 3초 대기
  - 완료 이벤트 발생
```

### 4. MainWindow.axaml (수정)

```xml
- TransitioningContentControl로 변경
- PageTransition: CrossFade (Duration 0.6초)
- Content 바인딩: {Binding CurrentView}
```

### 5. ViewModels/MainWindowViewModel.cs (수정)

```csharp
- CurrentView 속성 (object 타입)
- 생성자에서 SplashScreen으로 초기화
- 3.5초 후 LandingPage로 전환
- 또는 SplashScreenViewModel 완료 이벤트 수신
```

### 6. App.axaml.cs (확인)

```csharp
- MainWindow의 DataContext 설정 확인
```

## 애니메이션 코드 예시

### 로고 페이드 인 + 이동

```xml
<Style Selector="StackPanel.logo">
  <Style.Animations>
    <Animation Duration="0:0:1" FillMode="Forward">
      <KeyFrame Cue="0%">
        <Setter Property="Opacity" Value="0"/>
        <Setter Property="TranslateTransform.Y" Value="-30"/>
      </KeyFrame>
      <KeyFrame Cue="100%">
        <Setter Property="Opacity" Value="1"/>
        <Setter Property="TranslateTransform.Y" Value="0"/>
      </KeyFrame>
    </Animation>
  </Style.Animations>
</Style>
```

### 버전 페이드 인 (지연)

```xml
<Style Selector="TextBlock.version">
  <Style.Animations>
    <Animation Duration="0:0:0.5" Delay="0:0:0.5" FillMode="Forward">
      <KeyFrame Cue="0%">
        <Setter Property="Opacity" Value="0"/>
      </KeyFrame>
      <KeyFrame Cue="100%">
        <Setter Property="Opacity" Value="1"/>
      </KeyFrame>
    </Animation>
  </Style.Animations>
</Style>
```

### ProgressRing (기본 회전)

```xml
<ProgressRing IsActive="True" 
              IsIndeterminate="True"
              Width="32" Height="32"
              Foreground="#3B82F6" />
```

## 구현 순서 (작은 단위)

1. SplashScreen.axaml 생성 - 기본 레이아웃
2. 로고 영역 구현 (아이콘 + 텍스트)
3. ProgressRing 추가
4. 버전 정보 텍스트 추가
5. 로고 애니메이션 정의
6. 버전 애니메이션 정의
7. SplashScreen.axaml.cs 생성
8. SplashScreenViewModel 생성
9. MainWindowViewModel 수정 - CurrentView 속성
10. MainWindow.axaml 수정 - TransitioningContentControl
11. 뷰 전환 로직 구현
12. Backend health check 통합
13. 테스트 및 타이밍 조정

### To-dos

- [ ] SplashScreen.axaml 생성 - 기본 레이아웃
- [ ] 로고 영역 구현 (아이콘 + 텍스트)
- [ ] ProgressRing 추가
- [ ] 버전 정보 텍스트 추가
- [ ] 로고 애니메이션 정의
- [ ] 버전 애니메이션 정의
- [ ] SplashScreen.axaml.cs 생성
- [ ] SplashScreenViewModel 생성
- [ ] MainWindowViewModel 수정 - CurrentView 속성
- [ ] MainWindow.axaml 수정 - TransitioningContentControl
- [ ] 뷰 전환 로직 구현
- [ ] Backend health check 통합
- [ ] 테스트 및 타이밍 조정