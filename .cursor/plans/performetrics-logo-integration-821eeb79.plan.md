<!-- 821eeb79-4d1a-4843-9f2d-61c9127a08a4 8cd0158a-f825-432d-b4d4-401496d0d0c6 -->
# PerforMetrics Logo Integration Plan

## 작업 개요

제공하신 PerforMetrics 로고 이미지를 애플리케이션 전체에 통합하되, 기존 파란색 톤의 색상 테마는 그대로 유지하옵니다.

## 주요 변경 파일

### 1. Assets 폴더 (이미지 저장)

- `PerforMetrics/Assets/performetrics-logo.png` - 제공하신 로고 이미지 저장
- `PerforMetrics/Assets/performetrics-icon.ico` - 창 아이콘용 파일 생성 (PNG에서 변환)

### 2. SplashScreen 업데이트

**파일**: `PerforMetrics/Views/SplashScreen.axaml`

현재 상태 (58-68줄):

```58:68:PerforMetrics/Views/SplashScreen.axaml
<PathIcon Data="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"
          Width="56" Height="56"
          Foreground="#3B82F6"
          HorizontalAlignment="Center" />

<TextBlock Text="PerforMetrics"
           FontSize="36"
           FontWeight="Bold"
           Foreground="#111827"
           HorizontalAlignment="Center" />
```

변경 후: Shield 아이콘을 로고 이미지로 교체하고 텍스트는 제거 또는 조정

### 3. LandingPage 헤더 업데이트

**파일**: `PerforMetrics/Views/LandingPage.axaml`

현재 상태 (249-256줄):

```249:256:PerforMetrics/Views/LandingPage.axaml
<PathIcon Data="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"
          Width="24" Height="24"
          Foreground="{StaticResource AccentBrush}" />
<TextBlock Text="PerforMetrics"
           FontSize="18"
           FontWeight="SemiBold"
           Foreground="{StaticResource TextPrimaryBrush}"
           VerticalAlignment="Center" />
```

변경 후: Shield 아이콘을 로고 이미지로 교체

### 4. MainWindow 아이콘 업데이트

**파일**: `PerforMetrics/Views/MainWindow.axaml`

현재 상태 (10줄):

```10:10:PerforMetrics/Views/MainWindow.axaml
Icon="/Assets/avalonia-logo.ico"
```

변경 후: 새로운 PerforMetrics 아이콘으로 변경

## 구현 순서

1. 로고 이미지를 Assets 폴더에 저장
2. 필요시 창 아이콘용 .ico 파일 생성
3. SplashScreen.axaml의 Shield 아이콘을 Image 컨트롤로 교체하여 로고 표시
4. LandingPage.axaml 헤더의 Shield 아이콘을 Image 컨트롤로 교체
5. MainWindow.axaml의 Icon 경로를 새 아이콘 파일로 변경
6. 애플리케이션 빌드 및 시각적 확인

## 주의사항

- 기존 색상 스킴 (#3B82F6 등)은 변경하지 않음
- 로고 이미지 크기와 비율을 각 위치에 맞게 조정
- Assets 폴더의 파일들은 PerforMetrics.csproj에 자동으로 포함됨 (AvaloniaResource)

### To-dos

- [ ] 로고 이미지를 Assets 폴더에 저장하고 창 아이콘 파일 생성
- [ ] SplashScreen.axaml의 Shield 아이콘을 로고 이미지로 교체
- [ ] LandingPage.axaml 헤더의 아이콘을 로고 이미지로 교체
- [ ] MainWindow.axaml의 창 아이콘을 새 로고 아이콘으로 변경