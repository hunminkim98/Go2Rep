<!-- 464b1e18-6158-4419-bb83-45b7deba9c53 f9300d8c-9d48-4d6a-a1c3-274517aa5e73 -->
# LoadingIndicators.Avalonia 적용

## 개요

현재 SplashScreen의 커스텀 PathIcon 기반 로딩 스피너를 LoadingIndicators.Avalonia 패키지의 Arcs 스타일로 교체하여 더 전문적이고 세련된 로딩 애니메이션 구현

## 구현 단계

### 1. NuGet 패키지 추가

**파일**: `PerforMetrics/PerforMetrics.csproj`

- `LoadingIndicators.Avalonia` 버전 11.0.11.1 패키지 추가
- 기존 Avalonia 11.3.6과 호환됨 (net6.0+ 지원)
```xml
<PackageReference Include="LoadingIndicators.Avalonia" Version="11.0.11.1" />
```


### 2. 애플리케이션 리소스 등록

**파일**: `PerforMetrics/App.axaml`

- Application.Resources 섹션에 LoadingIndicators 리소스 포함
- ResourceInclude를 MergedDictionaries에 추가
```xml
<Application.Resources>
    <ResourceDictionary>
        <ResourceDictionary.MergedDictionaries>
            <ResourceInclude Source="avares://LoadingIndicators.Avalonia/LoadingIndicators.axaml" />
        </ResourceDictionary.MergedDictionaries>
        <!-- 기존 converters 유지 -->
    </ResourceDictionary>
</Application.Resources>
```


### 3. SplashScreen UI 교체 및 배치 개선

**파일**: `PerforMetrics/Views/SplashScreen.axaml`

**변경 사항**:

- xmlns에 `li="using:LoadingIndicators.Avalonia"` 네임스페이스 추가
- 커스텀 loading-spinner 스타일 제거 (43-55줄)
- 커스텀 Border 스피너 제거 (86-97줄)
- LoadingIndicator 컴포넌트로 교체

**전문적인 배치 원칙**:

- 로고와 인디케이터 간격: 48px (시각적 균형)
- 인디케이터 크기: 56px (중간 크기, 로고와 조화)
- Arcs 모드 사용
- Foreground="#3B82F6" (기존 브랜드 컬러 유지)
- IsActive 바인딩으로 ViewModel의 IsLoading 속성 연결
- SpeedRatio="1.0" (기본 속도, 부드러운 느낌)

**교체 코드**:

```xml
<!-- Loading Indicator -->
<li:LoadingIndicator IsActive="{Binding IsLoading}"
                     Mode="Arcs"
                     SpeedRatio="1.0"
                     Foreground="#3B82F6"
                     Width="56" Height="56"
                     HorizontalAlignment="Center" />
```

## 주요 파일

- `PerforMetrics/PerforMetrics.csproj`: 패키지 참조 추가
- `PerforMetrics/App.axaml`: 리소스 등록
- `PerforMetrics/Views/SplashScreen.axaml`: UI 교체 및 배치
- `PerforMetrics/ViewModels/SplashScreenViewModel.cs`: 이미 IsLoading 속성 존재 (변경 불필요)

## 예상 결과

- 9가지 전문 애니메이션 중 Arcs 스타일 적용
- 여러 개의 원호가 부드럽게 회전하는 세련된 로딩 효과
- ViewModel의 IsLoading 상태와 자동 연동
- 기존 브랜드 컬러와 조화로운 시각적 일관성

### To-dos

- [ ] PerforMetrics.csproj에 LoadingIndicators.Avalonia 패키지 추가
- [ ] App.axaml에 LoadingIndicators 리소스 등록
- [ ] SplashScreen.axaml에서 커스텀 스피너를 LoadingIndicator로 교체 및 전문적 배치