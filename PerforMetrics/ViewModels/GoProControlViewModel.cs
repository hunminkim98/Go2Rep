/* ===== using 지시문 (Python의 import와 동일) ===== 
 * C#에서는 using을 통해 다른 네임스페이스의 클래스를 가져옵니다.
 * Python: from module import Class 또는 import module
 * C#: using Namespace;
 */

using System; // 기본 시스템 타입들 (Exception, DateTime 등) - Python의 built-in과 유사
using System.Collections.Generic; // List<T>, Dictionary<K,V> 등 제네릭 컬렉션 - Python의 list, dict와 유사하지만 타입이 지정됨
using System.Collections.ObjectModel; // ObservableCollection<T> - 변경 사항을 자동으로 UI에 알려주는 특별한 컬렉션
using System.Linq; // LINQ 쿼리 기능 - Python의 filter, map, list comprehension과 유사한 기능 제공
using System.Threading.Tasks; // 비동기 프로그래밍 (Task, async/await) - Python의 asyncio와 유사
using System.Timers; // Timer 클래스 - 주기적으로 작업 실행, Python의 threading.Timer와 유사
using Avalonia.Controls; // Avalonia UI 컨트롤 (Window, Dialog 등) - GUI 프레임워크
using Avalonia.Threading; // UI 스레드 관리 (Dispatcher) - UI 업데이트는 반드시 UI 스레드에서 실행되어야 함
using CommunityToolkit.Mvvm.ComponentModel; // MVVM 패턴 지원 - [ObservableProperty] 등의 속성 제공
using CommunityToolkit.Mvvm.Input; // 커맨드 패턴 지원 - [RelayCommand] 속성 제공
using PerforMetrics.Models; // 우리 프로젝트의 데이터 모델 (GoProDevice 등)
using PerforMetrics.Services; // 우리 프로젝트의 서비스 계층 (ApiService 등)
using PerforMetrics.Views; // 우리 프로젝트의 View (UI) 클래스들

/* ===== namespace (네임스페이스) =====
 * C#의 네임스페이스는 클래스들을 논리적으로 그룹화하는 방법입니다.
 * Python의 패키지/모듈 개념과 유사하지만, 더 명시적입니다.
 * 예: PerforMetrics.ViewModels는 PerforMetrics 프로젝트의 ViewModels 폴더를 나타냅니다.
 */
namespace PerforMetrics.ViewModels;

/* ===== MVVM 패턴 (Model-View-ViewModel) =====
 * MVVM은 UI 애플리케이션을 구조화하는 디자인 패턴입니다.
 * 
 * Model: 데이터와 비즈니스 로직 (예: GoProDevice 클래스)
 * View: 사용자에게 보이는 UI (예: GoProControlView.axaml)
 * ViewModel: View와 Model을 연결하는 중간 계층 (이 클래스!)
 * 
 * Python과 비교:
 * - Python에서는 MVC 패턴이 더 일반적 (Django, Flask 등)
 * - MVVM의 ViewModel은 MVC의 Controller와 유사하지만, 데이터 바인딩이 핵심
 * - View와 ViewModel은 데이터 바인딩으로 자동 연결되어, 한쪽이 변경되면 다른 쪽도 자동 업데이트
 */

/// <summary>
/// ViewModel for GoPro Control page
/// GoPro 제어 페이지의 ViewModel
/// 이 클래스는 UI(View)와 데이터/로직을 연결하는 역할을 합니다
/// </summary>
/// 
/* ===== partial class 키워드 =====
 * C#의 partial 키워드는 하나의 클래스를 여러 파일에 나누어 작성할 수 있게 합니다.
 * Python에는 이런 개념이 없습니다.
 * 
 * 여기서 partial을 사용하는 이유:
 * - CommunityToolkit.Mvvm이 컴파일 시점에 자동으로 추가 코드를 생성하기 때문
 * - [ObservableProperty]와 [RelayCommand] 속성이 자동으로 public 프로퍼티와 메서드를 생성
 * - 예: private _isLoading 필드 → public IsLoading 프로퍼티가 자동 생성됨
 */
/// 
/* ===== 상속 (Inheritance) =====
 * : ViewModelBase는 이 클래스가 ViewModelBase를 상속받는다는 의미입니다.
 * Python과 비교:
 * - Python: class GoProControlViewModel(ViewModelBase):
 * - C#: class GoProControlViewModel : ViewModelBase
 * 
 * ViewModelBase는 모든 ViewModel의 기본 기능을 제공하는 부모 클래스입니다.
 */
public partial class GoProControlViewModel : ViewModelBase
{
    /* ===== 필드 (Field) 선언부 =====
     * 필드는 클래스의 데이터를 저장하는 변수입니다.
     * Python의 self.variable과 유사하지만, 접근 제한자(public, private)를 명시합니다.
     */

    /* ===== readonly 키워드 =====
     * readonly는 필드가 생성자에서만 값을 할당받을 수 있고, 이후에는 변경 불가능함을 의미합니다.
     * Python과 비교:
     * - Python에는 정확히 대응되는 개념이 없지만, 관례적으로 상수는 대문자로 작성
     * - Python: CONSTANT_VALUE = 42 (관례상 변경하지 않음)
     * - C#: private readonly int _constantValue = 42; (컴파일러가 변경 방지)
     */
    private readonly ApiService _apiService; // API 통신 서비스 객체 - 한 번 생성되면 변경되지 않음
    private readonly SettingsService _settingsService; // 설정 관리 서비스 객체
    
    /* C# 명명 규칙:
     * - private 필드는 언더스코어(_)로 시작하고 camelCase 사용: _apiService
     * - public 프로퍼티는 PascalCase 사용: ApiService
     * - Python은 보통 snake_case: api_service
     */
    
    /* ===== COHN 방식에서는 Health Check 타이머 불필요 =====
     * BLE 방식에서는 주기적인 연결 상태 체크를 위해 타이머를 사용했지만,
     * COHN(HTTP) 방식에서는 요청 실패 시 즉시 에러를 알 수 있으므로
     * 타이머가 필요하지 않습니다. 따라서 이 필드는 주석 처리합니다.
     * 
     * 기존 BLE 방식 코드:
     * private readonly Timer? _connectionHealthTimer;
     */
    
    /* ===== Nullable 타입 (?) =====
     * C#에서 ?는 해당 타입이 null 값을 가질 수 있음을 나타냅니다.
     * 
     * - Window?: null일 수 있는 Window 타입
     * - Window: null일 수 없는 Window 타입 (C# 8.0 이상의 nullable reference types 기능)
     * 
     * Python과 비교:
     * - Python은 모든 변수가 기본적으로 None(null)이 될 수 있습니다
     * - Python: owner_window: Optional[Window] = None (typing 모듈 사용 시)
     * - C#: Window? _ownerWindow; (컴파일러가 null 체크를 강제)
     */
    private Window? _ownerWindow; // 다이얼로그를 띄우기 위한 부모 윈도우 (처음엔 null이고 나중에 설정됨)
    
    /* ===== Null 조건 연산자들 =====
     * C#에는 null을 안전하게 처리하기 위한 여러 연산자가 있습니다:
     * 
     * 1) ?. (Null-conditional operator)
     *    - _ownerWindow?.Title
     *    - _ownerWindow가 null이면 아무 것도 하지 않고 null 반환
     *    - _ownerWindow가 null이 아니면 Title 속성에 접근
     *    - Python: getattr(owner_window, 'title', None) 또는 owner_window.title if owner_window else None
     * 
     * 2) ?? (Null-coalescing operator)
     *    - var title = _ownerWindow?.Title ?? "기본 제목"
     *    - 왼쪽이 null이면 오른쪽 값을 사용
     *    - Python: title = owner_window.title if owner_window else "기본 제목"
     *    - Python: title = getattr(owner_window, 'title', None) or "기본 제목"
     * 
     * 3) ! (Null-forgiving operator)
     *    - var title = _ownerWindow!.Title
     *    - 개발자가 "이 변수는 절대 null이 아니야!"라고 컴파일러에게 선언
     *    - 만약 실제로 null이면 NullReferenceException 발생
     *    - Python에는 이런 개념이 없음 (런타임에 AttributeError 발생)
     */

    /* ===== [ObservableProperty] 속성 (Attribute) =====
     * C#에서 대괄호 []로 감싼 것을 "속성(Attribute)"이라고 합니다.
     * Python의 데코레이터(@property)와 유사한 개념입니다.
     * 
     * [ObservableProperty]가 하는 일:
     * 1) 컴파일 시점에 자동으로 public 프로퍼티를 생성
     *    예: private _isLoading → public IsLoading { get; set; }
     * 
     * 2) 값이 변경될 때 자동으로 PropertyChanged 이벤트 발생
     *    → UI가 이 이벤트를 감지하고 자동으로 업데이트됨 (데이터 바인딩)
     * 
     * 3) INotifyPropertyChanged 인터페이스를 자동으로 구현
     * 
     * Python과 비교:
     * - Python: @property 데코레이터로 getter/setter 정의
     * - C#: [ObservableProperty]로 자동 생성 + 이벤트 발생까지 자동 처리
     * 
     * Python 예시:
     * class ViewModel:
     *     def __init__(self):
     *         self._is_loading = False
     *     
     *     @property
     *     def is_loading(self):
     *         return self._is_loading
     *     
     *     @is_loading.setter
     *     def is_loading(self, value):
     *         self._is_loading = value
     *         self.notify_ui()  # 수동으로 UI에 알림
     * 
     * C# 예시 (자동 생성됨):
     * public bool IsLoading
     * {
     *     get => _isLoading;
     *     set
     *     {
     *         if (_isLoading != value)
     *         {
     *             _isLoading = value;
     *             OnPropertyChanged(nameof(IsLoading));  # 자동으로 UI에 알림
     *         }
     *     }
     * }
     */

    /* ===== ObservableCollection<T> =====
     * ObservableCollection은 컬렉션(리스트)의 변경 사항을 자동으로 UI에 알려주는 특별한 컬렉션입니다.
     * 
     * - 일반 List<T>: 항목 추가/삭제해도 UI가 자동으로 업데이트 안 됨
     * - ObservableCollection<T>: 항목 추가/삭제하면 UI가 자동으로 업데이트됨
     * 
     * Python과 비교:
     * - Python의 list는 변경 시 자동 통지 기능이 없음
     * - Python에서 비슷한 기능을 구현하려면 Observer 패턴을 직접 구현하거나
     *   PyQt의 QAbstractListModel 같은 것을 사용해야 함
     */
    [ObservableProperty]
    private ObservableCollection<GoProDevice> _goProDevices; // GoPro 장치 목록 (UI 리스트와 자동 동기화)

    [ObservableProperty]
    private bool _isLoading; // 로딩 중 여부 (true면 UI에 로딩 스피너 표시)

    [ObservableProperty]
    private string _statusMessage = ""; // 상태 메시지 (UI 하단에 표시되는 텍스트)
    // C#에서 = ""는 초기값 설정 (Python의 __init__에서 self.status_message = ""와 동일)

    [ObservableProperty]
    private int _selectedFps = 120; // 선택된 FPS 값 (기본값 120)

    [ObservableProperty]
    private int _selectedResolution = 2700; // 선택된 해상도 값 (기본값 2700)

    [ObservableProperty]
    private bool _isBleMode = true; // BLE 모드 여부 (true=BLE, false=COHN)

    /* ===== 생성자 (Constructor) =====
     * 생성자는 클래스의 인스턴스가 생성될 때 자동으로 호출되는 특별한 메서드입니다.
     * 
     * Python과 비교:
     * - Python: def __init__(self):
     * - C#: public 클래스명()
     * 
     * 특징:
     * - 메서드 이름이 클래스 이름과 동일
     * - 반환 타입이 없음 (void도 쓰지 않음)
     * - 객체 초기화 작업을 수행
     */
    public GoProControlViewModel()
    {
        /* ===== new 키워드 =====
         * new는 새로운 객체 인스턴스를 생성합니다.
         * Python과 비교:
         * - Python: api_service = ApiService()
         * - C#: _apiService = new ApiService();
         * 
         * C#에서는 반드시 new 키워드를 명시해야 합니다.
         */
        _apiService = new ApiService(); // ApiService 객체 생성
        _settingsService = new SettingsService(); // SettingsService 객체 생성
        _goProDevices = new ObservableCollection<GoProDevice>(); // 빈 컬렉션 생성
        
        /* ===== COHN 방식에서는 Health Check 타이머 불필요 =====
         * COHN은 HTTP 기반이므로 요청 실패 시 즉시 에러를 알 수 있습니다.
         * 따라서 주기적인 연결 상태 확인이 필요없습니다.
         * 
         * 기존 BLE 방식의 타이머 코드는 주석 처리하여 보존합니다.
         */
        
        // BLE 방식의 Health Check 타이머 (COHN에서는 사용 안 함)
        // _connectionHealthTimer = new Timer(5000);
        // _connectionHealthTimer.Elapsed += async (sender, e) => await CheckConnectionHealthAsync();
        // _connectionHealthTimer.AutoReset = true;
        // _connectionHealthTimer.Start();
    }

    /// <summary>
    /// Set the owner window for showing dialogs
    /// 다이얼로그를 표시하기 위한 부모 윈도우를 설정합니다
    /// </summary>
    /// <param name="ownerWindow">부모 윈도우 객체</param>
    /* ===== public 메서드 =====
     * public 키워드는 이 메서드를 외부에서 호출할 수 있게 합니다.
     * Python과 비교:
     * - Python: 기본적으로 모든 메서드가 public (관례상 _로 시작하면 private)
     * - C#: 명시적으로 public, private, protected 등을 지정
     * 
     * void: 반환값이 없음 (Python의 return 없는 함수와 동일)
     */
    public void SetOwnerWindow(Window ownerWindow)
    {
        _ownerWindow = ownerWindow; // 매개변수로 받은 윈도우를 필드에 저장
    }

    /* ===== [RelayCommand] 속성 =====
     * [RelayCommand]는 메서드를 UI에서 호출 가능한 커맨드로 자동 변환합니다.
     * 
     * 이 속성이 하는 일:
     * 1) private async Task ScanDevicesAsync() 메서드를 감지
     * 2) 자동으로 public ICommand ScanDevicesCommand { get; } 프로퍼티 생성
     * 3) UI에서 이 커맨드를 버튼 등에 바인딩 가능
     *    예: <Button Command="{Binding ScanDevicesCommand}" />
     * 
     * 명명 규칙:
     * - 메서드 이름: ScanDevicesAsync
     * - 생성되는 커맨드: ScanDevicesCommand (Async 제거, Command 추가)
     * 
     * Python과 비교:
     * - Python의 GUI 프레임워크(PyQt, Tkinter)에서는 보통 직접 메서드를 연결
     * - Python: button.clicked.connect(self.scan_devices)
     * - C#: <Button Command="{Binding ScanDevicesCommand}" />
     * 
     * C#의 장점:
     * - 커맨드는 활성화/비활성화 상태를 자동으로 관리
     * - 비동기 작업 중 버튼 자동 비활성화 등의 기능 제공
     */
    
    /// <summary>
    /// Scan for available GoPro devices
    /// 사용 가능한 GoPro 장치를 검색합니다
    /// </summary>
    [RelayCommand] // 이 메서드를 UI 커맨드로 변환
    private async Task ScanDevicesAsync() // async: 비동기 메서드, Task: 비동기 작업을 나타내는 반환 타입
    {
        /* ===== async/await 패턴 =====
         * async와 await는 C#의 비동기 프로그래밍 핵심 키워드입니다.
         * 
         * Python과 비교:
         * - Python: async def scan_devices(self): ... await api_service.scan()
         * - C#: private async Task ScanDevicesAsync() { ... await _apiService.ScanAsync() }
         * 
         * 차이점:
         * - Python: asyncio 라이브러리 필요, 이벤트 루프 관리 필요
         * - C#: 언어 자체에 내장, Task 기반 비동기 모델 (TAP)
         * 
         * Task:
         * - Task는 비동기 작업을 나타내는 객체
         * - Task<T>는 T 타입의 결과를 반환하는 비동기 작업
         * - Task (제네릭 없음)는 결과가 없는 비동기 작업 (Python의 async def 함수와 유사)
         * 
         * 비동기가 중요한 이유:
         * - UI 스레드를 차단하지 않고 긴 작업 수행
         * - 네트워크 요청, 파일 I/O 등을 기다리는 동안 UI가 멈추지 않음
         * - Python의 await asyncio.sleep()과 유사하게 await Task.Delay() 가능
         */
        
        // IsLoading 프로퍼티에 값 할당 (자동으로 UI에 알림이 전달됨)
        IsLoading = true; // 로딩 시작 → UI에 로딩 스피너 표시
        StatusMessage = "장치를 검색하는 중..."; // 상태 메시지 업데이트 → UI에 자동 반영
        
        /* ===== 문자열 보간 (String Interpolation) =====
         * C#에서는 $ 기호로 시작하는 문자열에서 변수를 직접 삽입할 수 있습니다.
         * Python과 비교:
         * - Python: f"발견: {count}개" 또는 "발견: {}개".format(count)
         * - C#: $"발견: {count}개"
         * 
         * 예시:
         * var name = "홍길동";
         * var age = 30;
         * var message = $"{name}님의 나이는 {age}세입니다.";
         */

        /* ===== try-catch-finally =====
         * 예외 처리 구문입니다.
         * Python과 비교:
         * - Python: try: ... except Exception as ex: ... finally: ...
         * - C#: try { ... } catch (Exception ex) { ... } finally { ... }
         * 
         * 차이점:
         * - Python: 콜론(:)과 들여쓰기로 블록 구분
         * - C#: 중괄호({})로 블록 구분
         * - Python: except ExceptionType as var
         * - C#: catch (ExceptionType var)
         */
        try
        {
            /* ===== 타입 선언 (Type Declaration) =====
             * C#은 정적 타입 언어이므로 변수 타입을 명시해야 합니다.
             * 
             * List<GoProDevice>?의 의미:
             * - List<T>: T 타입 객체들의 리스트 (Python의 list[T]와 유사)
             * - <GoProDevice>: 제네릭 타입 매개변수 (Python의 list[GoProDevice])
             * - ?: nullable 타입 (null을 허용)
             * 
             * Python과 비교:
             * - Python: devices: Optional[List[GoProDevice]] = None
             * - C#: List<GoProDevice>? devices;
             */
            List<GoProDevice>? devices; // devices 변수 선언 (아직 값 할당 안 됨)
            
            /* ===== 조건문 (if-else) =====
             * Python과 비교:
             * - Python: if condition: ... else: ...
             * - C#: if (condition) { ... } else { ... }
             */
            if (IsBleMode) // IsBleMode는 자동 생성된 public 프로퍼티 (실제로는 _isBleMode 필드 접근)
            {
                /* ===== await 키워드 =====
                 * await는 비동기 작업이 완료될 때까지 기다립니다.
                 * 
                 * Python과 비교:
                 * - Python: devices = await api_service.scan_gopro_devices_async()
                 * - C#: devices = await _apiService.ScanGoProDevicesAsync();
                 * 
                 * 중요한 점:
                 * - await를 사용해도 UI 스레드는 차단되지 않음
                 * - 작업이 완료되면 이 지점부터 다시 실행 재개
                 * - await 없이 호출하면 Task 객체만 반환되고 작업 완료를 기다리지 않음
                 */
                devices = await _apiService.ScanGoProDevicesAsync(); // BLE 스캔 실행 (비동기)
                StatusMessage = "BLE 스캔 완료";
            }
            else
            {
                devices = await _apiService.GetCOHNDevicesAsync(); // COHN 장치 검색 (비동기)
                StatusMessage = "COHN 장치 검색 완료";
            }

            /* ===== null 체크와 LINQ 메서드 =====
             * devices != null: devices가 null이 아닌지 확인
             * devices.Any(): 컬렉션에 요소가 하나라도 있는지 확인
             * 
             * LINQ (Language Integrated Query):
             * - .NET의 강력한 쿼리 기능
             * - Python의 filter, map, any, all과 유사한 메서드 제공
             * 
             * Python과 비교:
             * - Python: if devices is not None and len(devices) > 0:
             * - Python: if devices and any(devices):
             * - C#: if (devices != null && devices.Any())
             * 
             * &&: 논리 AND 연산자 (Python의 and)
             * ||: 논리 OR 연산자 (Python의 or)
             * !: 논리 NOT 연산자 (Python의 not)
             */
            if (devices != null && devices.Any())
            {
                GoProDevices.Clear(); // 기존 목록 비우기 (Python의 list.clear())
                
                /* ===== foreach 반복문 =====
                 * Python과 비교:
                 * - Python: for device in devices:
                 * - C#: foreach (var device in devices)
                 * 
                 * var 키워드:
                 * - 컴파일러가 자동으로 타입을 추론
                 * - var device = ... → GoProDevice device = ... 와 동일
                 * - Python은 모든 변수가 동적 타입이지만, C#의 var는 컴파일 시점에 타입 결정
                 */
                foreach (var device in devices)
                {
                    GoProDevices.Add(device); // 컬렉션에 장치 추가
                }
                
                // $"..." 문자열 보간을 사용하여 동적 메시지 생성
                StatusMessage = $"{devices.Count}개의 장치를 발견했습니다";
                // Python: f"{len(devices)}개의 장치를 발견했습니다"
            }
            else
            {
                StatusMessage = "장치를 찾을 수 없습니다";
            }
        }
        catch (Exception ex) // 모든 예외를 잡아서 ex 변수에 저장
        {
            // ex.Message: 예외 메시지 (Python의 str(ex)와 유사)
            StatusMessage = $"스캔 실패: {ex.Message}";
        }
        finally // 예외 발생 여부와 관계없이 항상 실행되는 블록
        {
            IsLoading = false; // 로딩 종료 → UI에서 로딩 스피너 숨김
            // finally는 리소스 정리, 상태 복원 등에 사용
            // Python의 finally와 동일
        }
    }

    /// <summary>
    /// Start recording on all connected devices
    /// 연결된 모든 장치에서 녹화를 시작합니다
    /// </summary>
    [RelayCommand]
    private async Task StartAllRecordingAsync()
    {
        IsLoading = true; // 로딩 상태 활성화
        StatusMessage = "전체 녹화를 시작하는 중...";

        try
        {
            /* ===== LINQ 쿼리 체이닝 (Method Chaining) =====
             * LINQ는 컬렉션을 쿼리하고 변환하는 강력한 기능입니다.
             * 여러 메서드를 체이닝하여 복잡한 쿼리를 간결하게 작성할 수 있습니다.
             * 
             * Python과 비교:
             * Python에서 동일한 작업을 하려면:
             * connected_ids = [
             *     device.identifier 
             *     for device in go_pro_devices 
             *     if device.connected
             * ]
             * 또는
             * connected_ids = list(
             *     map(lambda d: d.identifier,
             *         filter(lambda d: d.connected, go_pro_devices))
             * )
             * 
             * C# LINQ:
             * var connectedIds = GoProDevices
             *     .Where(d => d.Connected)        # filter()와 유사
             *     .Select(d => d.Identifier)      # map()과 유사
             *     .ToList();                      # list()로 변환
             * 
             * LINQ의 장점:
             * - 가독성이 좋음 (각 단계가 명확함)
             * - 지연 실행(Lazy Evaluation): ToList() 호출 전까지 실제로 실행 안 됨
             * - 메서드 체이닝으로 복잡한 변환을 단계별로 표현
             */
            
            /* ===== Where 메서드 =====
             * Where는 조건을 만족하는 요소만 필터링합니다.
             * Python의 filter()와 동일합니다.
             * 
             * d => d.Connected:
             * - 람다식으로, 각 요소(d)에 대해 d.Connected가 true인지 확인
             * - Python: lambda d: d.connected
             */
            
            /* ===== Select 메서드 =====
             * Select는 각 요소를 변환합니다.
             * Python의 map()과 동일합니다.
             * 
             * d => d.Identifier:
             * - 람다식으로, 각 장치 객체(d)를 Identifier 문자열로 변환
             * - Python: lambda d: d.identifier
             */
            
            /* ===== ToList 메서드 =====
             * ToList()는 LINQ 쿼리 결과를 List<T>로 변환합니다.
             * 이 시점에 실제로 쿼리가 실행됩니다 (지연 실행의 종료).
             * 
             * Python: list(iterator) 또는 [x for x in iterator]
             */
            var connectedIds = GoProDevices       // ObservableCollection<GoProDevice>에서 시작
                .Where(d => d.Connected)           // 연결된 장치만 필터링
                .Select(d => d.Identifier)         // 각 장치의 Identifier만 추출
                .ToList();                         // List<string>으로 변환
            // 결과: 연결된 장치들의 Identifier 문자열 리스트

            /* ===== ! (논리 NOT 연산자) =====
             * !는 불리언 값을 반전시킵니다.
             * Python: not
             * 
             * !connectedIds.Any()
             * = connectedIds.Any()가 false일 때 true
             * = 리스트가 비어있을 때 true
             */
            if (!connectedIds.Any()) // Any(): 요소가 하나라도 있으면 true (Python: bool(list) 또는 len(list) > 0)
            {
                StatusMessage = "연결된 장치가 없습니다";
                
                /* ===== return 문 =====
                 * return은 메서드를 즉시 종료하고 호출자에게 돌아갑니다.
                 * Task를 반환하는 메서드에서 return;만 쓰면 완료된 Task를 반환합니다.
                 * Python과 동일: return
                 */
                return; // 메서드 종료 (finally 블록은 실행됨)
            }

            /* ===== 명명된 인자 (Named Arguments) 형식이 아닌 일반 인자 =====
             * C#에서 메서드 호출 시 인자를 순서대로 전달하거나, 이름을 명시할 수 있습니다.
             * 
             * 일반 형식: _apiService.ControlRecordingAsync("start", connectedIds)
             * 명명된 형식: _apiService.ControlRecordingAsync(action: "start", identifiers: connectedIds)
             * 
             * Python과 비교:
             * - Python: api_service.control_recording_async("start", connected_ids)
             * - Python: api_service.control_recording_async(action="start", identifiers=connected_ids)
             * - C#도 Python과 유사하게 위치 인자와 명명된 인자를 모두 지원
             */
            bool success = await _apiService.ControlRecordingAsync("start", connectedIds);
            // "start": 녹화 시작 명령
            // connectedIds: 대상 장치 목록
            // 반환값: bool (성공 여부)
            
            if (success)
            {
                StatusMessage = $"{connectedIds.Count}개 장치에서 녹화 시작";
                // connectedIds.Count: 리스트의 요소 개수 (Python의 len(connected_ids))
            }
            else
            {
                StatusMessage = "녹화 시작 실패";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"녹화 시작 오류: {ex.Message}";
        }
        finally
        {
            IsLoading = false; // 로딩 상태 비활성화 (예외 발생 여부와 관계없이 실행)
        }
    }

    /// <summary>
    /// Stop recording on all connected devices
    /// 연결된 모든 장치에서 녹화를 중지합니다
    /// </summary>
    [RelayCommand]
    private async Task StopAllRecordingAsync()
    {
        // 이 메서드는 StartAllRecordingAsync와 거의 동일한 구조입니다
        // 차이점: "start" 대신 "stop" 명령을 전송
        IsLoading = true;
        StatusMessage = "전체 녹화를 중지하는 중...";

        try
        {
            // LINQ로 연결된 장치들의 ID만 추출 (StartAllRecordingAsync와 동일한 패턴)
            var connectedIds = GoProDevices
                .Where(d => d.Connected)
                .Select(d => d.Identifier)
                .ToList();

            if (!connectedIds.Any())
            {
                StatusMessage = "연결된 장치가 없습니다";
                return;
            }

            bool success = await _apiService.ControlRecordingAsync("stop", connectedIds);
            // "stop": 녹화 중지 명령
            
            if (success)
            {
                StatusMessage = $"{connectedIds.Count}개 장치에서 녹화 중지";
            }
            else
            {
                StatusMessage = "녹화 중지 실패";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"녹화 중지 오류: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    /// <summary>
    /// Toggle recording for a specific device
    /// 특정 장치의 녹화를 토글합니다 (켜기/끄기 전환)
    /// </summary>
    /// <param name="identifier">장치의 고유 식별자</param>
    [RelayCommand]
    private async Task ToggleDeviceRecordingAsync(string identifier)
    {
        // 이 메서드는 매개변수를 받습니다
        // UI에서 커맨드 호출 시 identifier를 전달합니다
        // 예: <Button Command="{Binding ToggleDeviceRecordingCommand}" CommandParameter="{Binding Identifier}" />
        
        IsLoading = true;
        StatusMessage = $"GoPro {identifier} 녹화 토글 중...";

        try
        {
            /* ===== FirstOrDefault 메서드 =====
             * FirstOrDefault는 조건을 만족하는 첫 번째 요소를 반환합니다.
             * 조건을 만족하는 요소가 없으면 default 값(참조 타입은 null)을 반환합니다.
             * 
             * Python과 비교:
             * - Python: next((d for d in devices if d.identifier == identifier), None)
             * - C#: GoProDevices.FirstOrDefault(d => d.Identifier == identifier)
             * 
             * 유사한 메서드들:
             * - First(): 요소가 없으면 예외 발생
             * - FirstOrDefault(): 요소가 없으면 null 반환
             * - Single(): 정확히 1개만 있어야 하고, 없거나 2개 이상이면 예외
             * - SingleOrDefault(): 0개 또는 1개만 허용, 2개 이상이면 예외
             */
            var device = GoProDevices.FirstOrDefault(d => d.Identifier == identifier);
            
            // || : 논리 OR 연산자 (Python의 or)
            if (device == null || !device.Connected)
            {
                StatusMessage = "장치가 연결되지 않았습니다";
                return;
            }

            // 현재는 항상 녹화 시작만 수행 (실제 토글 기능은 미구현)
            // 실제 구현에서는 장치의 녹화 상태를 추적하여 start/stop 결정
            
            /* ===== 컬렉션 초기화 구문 =====
             * new List<string> { identifier }
             * = identifier 하나만 들어있는 새 리스트 생성
             * 
             * Python과 비교:
             * - Python: [identifier]
             * - C#: new List<string> { identifier }
             * 
             * 더 많은 요소 예시:
             * - Python: ["id1", "id2", "id3"]
             * - C#: new List<string> { "id1", "id2", "id3" }
             */
            bool success = await _apiService.ControlRecordingAsync("start", new List<string> { identifier });
            
            if (success)
            {
                StatusMessage = $"GoPro {identifier} 녹화 시작";
            }
            else
            {
                StatusMessage = $"GoPro {identifier} 녹화 실패";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"녹화 토글 오류: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    /// <summary>
    /// Open settings for a specific device
    /// 특정 장치의 설정 화면을 엽니다
    /// </summary>
    /// <param name="identifier">장치의 고유 식별자</param>
    [RelayCommand]
    private void OpenDeviceSettings(string identifier)
    {
        // 이 메서드는 비동기가 아닙니다 (async 없음)
        // 반환 타입이 void (Task가 아님)
        StatusMessage = $"GoPro {identifier} 설정 열기";
        // TODO: Implement settings dialog
        // TODO는 C#에서 작업 표시자로 사용되며, Visual Studio에서 TODO 목록에 표시됨
    }

    /// <summary>
    /// Apply quick settings to all connected devices
    /// 연결된 모든 장치에 빠른 설정을 적용합니다
    /// </summary>
    [RelayCommand]
    private async Task ApplyQuickSettingsAsync()
    {
        IsLoading = true;
        StatusMessage = "설정을 적용하는 중...";

        try
        {
            // LINQ로 연결된 장치 ID 목록 추출 (이제는 익숙한 패턴!)
            var connectedIds = GoProDevices
                .Where(d => d.Connected)
                .Select(d => d.Identifier)
                .ToList();

            if (!connectedIds.Any())
            {
                StatusMessage = "연결된 장치가 없습니다";
                return;
            }

            /* ===== 명명된 인자 (Named Arguments) =====
             * 메서드 호출 시 매개변수 이름을 명시하여 인자를 전달할 수 있습니다.
             * 
             * 장점:
             * - 가독성 향상 (어떤 값이 어떤 매개변수에 전달되는지 명확)
             * - 순서 무관 (named arguments를 사용하면 순서를 바꿀 수 있음)
             * - 선택적 매개변수 활용 가능
             * 
             * Python과 비교:
             * - Python: api_service.change_settings_async(fps=120, resolution=2700, identifiers=ids)
             * - C#: _apiService.ChangeSettingsAsync(fps: 120, resolution: 2700, identifiers: ids)
             * 
             * 형식:
             * - 일반: Method(value1, value2, value3)
             * - 명명: Method(param1: value1, param2: value2, param3: value3)
             * - 혼합: Method(value1, param3: value3) # 위치 인자 후에 명명된 인자
             */
            bool success = await _apiService.ChangeSettingsAsync(
                fps: SelectedFps,                    // 명명된 인자: fps 매개변수에 SelectedFps 전달
                resolution: SelectedResolution,      // 명명된 인자: resolution 매개변수
                identifiers: connectedIds            // 명명된 인자: identifiers 매개변수
            );
            
            if (success)
            {
                StatusMessage = $"{connectedIds.Count}개 장치에 설정 적용 완료 (FPS: {SelectedFps}, 해상도: {SelectedResolution})";
            }
            else
            {
                StatusMessage = "설정 적용 실패";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"설정 적용 오류: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    /// <summary>
    /// Open global WiFi settings dialog
    /// 전역 WiFi 설정 다이얼로그를 엽니다
    /// </summary>
    [RelayCommand]
    private async Task OpenWiFiSettingsAsync()
    {
        if (_ownerWindow == null)
        {
            StatusMessage = "다이얼로그를 표시할 수 없습니다.";
            return;
        }

        try
        {
            // Load existing WiFi profiles
            var profiles = await _settingsService.LoadWiFiProfilesAsync();
            var profilesCollection = new ObservableCollection<WiFiProfile>(profiles);
            
            // Create dialog ViewModel
            var dialogViewModel = new WiFiProvisionDialogViewModel();
            dialogViewModel.LoadProfiles(profilesCollection);
            
            // If there are profiles, select the most recent one
            if (profiles.Any())
            {
                dialogViewModel.SelectedProfile = profiles.First();
            }

            var dialog = new WiFiProvisionDialog
            {
                DataContext = dialogViewModel
            };

            var result = await dialog.ShowDialog<bool?>(_ownerWindow);

            // User clicked confirm
            if (result == true)
            {
                if (!dialogViewModel.ValidateInput())
                {
                    StatusMessage = "WiFi 설정이 유효하지 않습니다.";
                    return;
                }

                // Save as WiFi profile
                var profile = new WiFiProfile
                {
                    Ssid = dialogViewModel.Ssid,
                    Password = dialogViewModel.Password
                };

                var (success, errorMessage) = await _settingsService.SaveWiFiProfileAsync(profile);

                if (success)
                {
                    StatusMessage = $"WiFi 프로필이 저장되었습니다: {profile.Ssid}";
                }
                else
                {
                    var filePath = _settingsService.GetSettingsFilePath();
                    StatusMessage = $"WiFi 설정 저장 실패: {errorMessage} (경로: {filePath})";
                }
            }
            else
            {
                StatusMessage = "WiFi 설정이 취소되었습니다.";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"WiFi 설정 오류: {ex.Message}";
        }
    }

    /// <summary>
    /// Connect to a specific device via COHN (WiFi provisioning)
    /// 특정 장치에 COHN (WiFi 프로비저닝)으로 연결합니다
    /// </summary>
    /// <param name="identifier">연결할 장치의 고유 식별자</param>
    [RelayCommand]
    private async Task ConnectDeviceAsync(string identifier)
    {
        if (_ownerWindow == null)
        {
            StatusMessage = "다이얼로그를 표시할 수 없습니다.";
            return;
        }

        try
        {
            string ssid = "";
            string password = "";

            // Try to load most recent WiFi profile
            var profiles = await _settingsService.LoadWiFiProfilesAsync();
            
            if (profiles.Any())
            {
                // Use most recent profile automatically
                var recentProfile = profiles.First();
                ssid = recentProfile.Ssid;
                password = recentProfile.Password;
                StatusMessage = $"저장된 WiFi 프로필을 사용합니다: {ssid}";
            }
            else
            {
                // No saved profiles, show dialog
                var dialogViewModel = new WiFiProvisionDialogViewModel(identifier);
                var dialog = new WiFiProvisionDialog
                {
                    DataContext = dialogViewModel
                };

                var result = await dialog.ShowDialog<bool?>(_ownerWindow);

                // User cancelled
                if (result != true)
                {
                    StatusMessage = "연결이 취소되었습니다.";
                    return;
                }

                ssid = dialogViewModel.Ssid;
                password = dialogViewModel.Password;
                
                // Save this as a new profile for next time
                var newProfile = new WiFiProfile
                {
                    Ssid = ssid,
                    Password = password
                };
                await _settingsService.SaveWiFiProfileAsync(newProfile);
            }

            // Start provisioning
            IsLoading = true;
            StatusMessage = $"GoPro {identifier} 프로비저닝 중... (약 30초 소요)";

            bool success = await _apiService.ProvisionGoProAsync(
                identifier, 
                ssid, 
                password
            );
            
            if (success)
            {
                // Update device connection status
                var device = GoProDevices.FirstOrDefault(d => d.Identifier == identifier);
                if (device != null)
                {
                    device.Connected = true;
                }
                StatusMessage = $"GoPro {identifier} 프로비저닝 완료! COHN으로 연결되었습니다.";
            }
            else
            {
                StatusMessage = $"GoPro {identifier} 프로비저닝 실패. WiFi 정보를 확인하세요.";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"프로비저닝 오류: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    /// <summary>
    /// Set FPS value from radio button
    /// 라디오 버튼에서 FPS 값을 설정합니다
    /// </summary>
    /// <param name="fps">FPS 값 (문자열)</param>
    [RelayCommand]
    private void SetFps(string fps)
    {
        /* ===== TryParse 메서드 (out 매개변수) =====
         * TryParse는 문자열을 숫자로 변환을 시도합니다.
         * 변환 성공 시 true 반환, 실패 시 false 반환합니다.
         * 
         * out 키워드:
         * - 메서드가 여러 값을 반환하고 싶을 때 사용
         * - out 매개변수는 메서드 내부에서 값을 할당해야 함
         * - 호출자는 out 매개변수를 통해 변환된 값을 받음
         * 
         * Python과 비교:
         * Python에는 out 매개변수가 없습니다. 대신:
         * - try-except로 변환 시도
         * - 튜플 반환으로 여러 값 반환
         * 
         * Python 예시:
         * try:
         *     fps_value = int(fps)
         *     selected_fps = fps_value
         * except ValueError:
         *     pass  # 변환 실패 시 아무것도 안 함
         * 
         * C# 예시:
         * if (int.TryParse(fps, out int fpsValue))
         * {
         *     SelectedFps = fpsValue;  # 변환 성공 시 실행
         * }
         * # 변환 실패 시 if 블록이 실행되지 않음
         * 
         * int.TryParse의 동작:
         * - 첫 번째 인자: 변환할 문자열
         * - 두 번째 인자 (out): 변환된 결과를 저장할 변수
         * - 반환값: 변환 성공 여부 (bool)
         * 
         * C# 7.0 이상에서는 out 변수를 인라인으로 선언 가능:
         * if (int.TryParse(fps, out int fpsValue))  # 여기서 fpsValue 선언
         */
        if (int.TryParse(fps, out int fpsValue)) // fps 문자열을 int로 변환 시도
        {
            SelectedFps = fpsValue; // 변환 성공 시 SelectedFps 업데이트
            // 변환 실패 시 이 블록은 실행되지 않고, SelectedFps는 이전 값 유지
        }
    }

    /// <summary>
    /// Set resolution value from radio button
    /// 라디오 버튼에서 해상도 값을 설정합니다
    /// </summary>
    /// <param name="resolution">해상도 값 (문자열)</param>
    [RelayCommand]
    private void SetResolution(string resolution)
    {
        // SetFps와 동일한 패턴 (TryParse 사용)
        if (int.TryParse(resolution, out int resValue)) // resolution 문자열을 int로 변환
        {
            SelectedResolution = resValue; // 변환 성공 시 SelectedResolution 업데이트
        }
    }

    /// <summary>
    /// Check connection health for all connected devices
    /// 연결된 모든 장치의 연결 상태를 확인합니다
    /// 
    /// COHN 방식에서는 이 메서드가 비활성화됩니다.
    /// HTTP 요청 실패 시 즉시 에러를 알 수 있으므로 주기적 체크가 불필요합니다.
    /// </summary>
    private async Task CheckConnectionHealthAsync()
    {
        // COHN 방식에서는 health check 불필요
        return;
        
        #pragma warning disable CS0162 // 접근할 수 없는 코드가 검색되었습니다.
        // 기존 BLE 방식 코드 (향후 참조용으로 보존)
        // 현재 로딩 중이거나 장치가 없으면 체크하지 않음
        if (IsLoading || !GoProDevices.Any()) return;

        // 연결이 끊긴 장치들을 저장할 리스트 생성
        var disconnectedDevices = new List<GoProDevice>();

        /* ===== LINQ 체이닝 + ToList()의 중요성 =====
         * GoProDevices.Where(d => d.Connected).ToList()
         * 
         * ToList()를 호출하는 이유:
         * - foreach 반복 중에 컬렉션이 수정될 수 있기 때문
         * - ToList()로 현재 시점의 스냅샷을 만들어 안전하게 반복
         * 
         * Python과 비교:
         * - Python: for device in list(filter(lambda d: d.connected, devices)):
         * - 또는: for device in [d for d in devices if d.connected]:
         * 
         * ToList() 없이 반복하면:
         * - 반복 중 컬렉션 수정 시 InvalidOperationException 발생
         * - "Collection was modified; enumeration operation may not execute"
         */
        // 연결된 각 장치의 상태를 확인
        foreach (var device in GoProDevices.Where(d => d.Connected).ToList())
        {
            try
            {
                // API를 통해 장치가 여전히 연결되어 있는지 확인
                bool isHealthy = await _apiService.CheckDeviceConnectionAsync(device.Identifier);
                
                if (!isHealthy) // 연결이 끊어진 경우
                {
                    /* ===== Dispatcher.UIThread.InvokeAsync =====
                     * UI 업데이트는 반드시 UI 스레드에서 실행되어야 합니다.
                     * 
                     * Dispatcher:
                     * - UI 스레드에서 작업을 실행하도록 예약하는 메커니즘
                     * - 백그라운드 스레드에서 UI를 직접 수정하면 예외 발생
                     * 
                     * Python과 비교:
                     * - PyQt: QMetaObject.invokeMethod() 또는 signals/slots
                     * - Tkinter: after() 메서드
                     * - asyncio: call_soon_threadsafe()
                     * 
                     * 왜 필요한가?
                     * - 이 메서드는 Timer 콜백에서 호출됨 (백그라운드 스레드)
                     * - UI 컨트롤은 생성된 스레드(UI 스레드)에서만 수정 가능
                     * - 다른 스레드에서 수정 시 크래시 또는 예외 발생
                     * 
                     * InvokeAsync:
                     * - () => { ... }: 람다식으로 UI 스레드에서 실행할 코드 정의
                     * - async: UI 스레드에서 비동기로 실행
                     * - await: 실행 완료까지 대기
                     */
                    // UI 스레드에서 장치 상태 업데이트
                    await Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        device.Connected = false; // 연결 상태를 false로 변경
                        device.LastHealthCheck = DateTime.Now; // 마지막 체크 시간 업데이트
                        disconnectedDevices.Add(device); // 연결 끊긴 장치 리스트에 추가
                    });
                }
                else // 여전히 연결되어 있는 경우
                {
                    // 마지막 체크 시간만 업데이트
                    await Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        /* ===== DateTime.Now =====
                         * DateTime.Now: 현재 시스템 시간
                         * Python과 비교:
                         * - Python: datetime.datetime.now()
                         * - C#: DateTime.Now
                         * 
                         * DateTime 타입:
                         * - 날짜와 시간을 표현하는 구조체
                         * - Year, Month, Day, Hour, Minute, Second 등의 속성 제공
                         * - Python의 datetime.datetime과 유사
                         */
                        device.LastHealthCheck = DateTime.Now;
                    });
                }
            }
            catch // 예외 타입을 명시하지 않으면 모든 예외를 잡음
            {
                /* ===== catch (예외 타입 없음) =====
                 * catch 블록에 예외 타입을 명시하지 않으면 모든 예외를 잡습니다.
                 * 
                 * Python과 비교:
                 * - Python: except:  (모든 예외)
                 * - Python: except Exception:  (대부분의 예외)
                 * - C#: catch  (모든 예외)
                 * - C#: catch (Exception)  (모든 예외, 변수로 접근 가능)
                 * 
                 * 여기서는 예외 타입을 명시하지 않았습니다:
                 * - 어떤 오류든 연결 끊김으로 간주
                 * - 네트워크 오류, 타임아웃, 기타 모든 오류 처리
                 */
                // 체크 실패 시 연결 끊긴 것으로 간주
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    device.Connected = false;
                    device.LastHealthCheck = DateTime.Now;
                    disconnectedDevices.Add(device);
                });
            }
        }

        // 연결이 끊긴 장치가 있으면 재연결 다이얼로그 표시
        if (disconnectedDevices.Any())
        {
            /* ===== 중첩 람다식과 async =====
             * await Dispatcher.UIThread.InvokeAsync(async () => { ... })
             * 
             * 분해:
             * 1) Dispatcher.UIThread.InvokeAsync: UI 스레드에서 코드 실행
             * 2) async () => { ... }: 비동기 람다식
             * 3) await ShowReconnectionDialogAsync: 람다식 내부에서 비동기 메서드 호출
             * 
             * 이 패턴이 필요한 이유:
             * - ShowReconnectionDialogAsync는 UI 스레드에서 실행되어야 함 (다이얼로그 표시)
             * - 동시에 비동기 메서드이므로 await 필요
             * - 따라서 InvokeAsync 내부의 람다식도 async여야 함
             */
            await Dispatcher.UIThread.InvokeAsync(async () =>
            {
                await ShowReconnectionDialogAsync(disconnectedDevices);
            });
        }
    }

    /// <summary>
    /// Show reconnection dialog for disconnected devices
    /// 연결이 끊긴 장치들에 대한 재연결 다이얼로그를 표시합니다
    /// </summary>
    /// <param name="disconnectedDevices">연결이 끊긴 장치 목록</param>
    private async Task ShowReconnectionDialogAsync(List<GoProDevice> disconnectedDevices)
    {
        // COHN 방식에서는 Health Check 타이머를 사용하지 않습니다
        // 기존 BLE 방식의 타이머 정지 코드 (주석 처리)
        // _connectionHealthTimer?.Stop();

        try
        {
            // owner window가 설정되어 있는지 확인
            // 다이얼로그를 표시하려면 부모 윈도우가 필요함
            if (_ownerWindow == null)
            {
                StatusMessage = "재연결 다이얼로그를 표시할 수 없습니다 (Owner Window 없음).";
                return;
            }

            /* ===== 다이얼로그 ViewModel 생성 =====
             * MVVM 패턴에서 다이얼로그도 ViewModel을 가집니다.
             * 
             * 패턴:
             * 1) ViewModel 생성: 다이얼로그에 필요한 데이터와 로직 포함
             * 2) View 생성: 실제 다이얼로그 창
             * 3) DataContext 연결: View와 ViewModel 바인딩
             * 4) ShowDialog: 모달 다이얼로그로 표시
             */
            // 재연결 다이얼로그의 ViewModel 생성
            // List를 ObservableCollection으로 변환하여 전달 (UI 바인딩을 위해)
            var viewModel = new ReconnectionDialogViewModel(
                new ObservableCollection<GoProDevice>(disconnectedDevices)
            );

            /* ===== 객체 초기화 구문 (Object Initializer) =====
             * C#에서는 객체 생성 시 중괄호 {}를 사용하여 속성을 초기화할 수 있습니다.
             * 
             * Python과 비교:
             * Python에는 이런 문법이 없습니다. 대신:
             * dialog = ReconnectionDialog()
             * dialog.data_context = view_model
             * 
             * C# 객체 초기화 구문:
             * var dialog = new ReconnectionDialog
             * {
             *     DataContext = viewModel,  // 속성1
             *     Width = 400,              // 속성2 (예시)
             *     Height = 300              // 속성3 (예시)
             * };
             * 
             * 위 코드는 다음과 동일합니다:
             * var dialog = new ReconnectionDialog();
             * dialog.DataContext = viewModel;
             * dialog.Width = 400;
             * dialog.Height = 300;
             * 
             * 장점:
             * - 간결하고 가독성 좋음
             * - 객체 생성과 초기화를 한 번에 수행
             */
            var dialog = new ReconnectionDialog
            {
                /* ===== DataContext =====
                 * DataContext는 View와 ViewModel을 연결하는 핵심 속성입니다.
                 * 
                 * 동작 방식:
                 * - View(XAML)의 바인딩 표현식 {Binding PropertyName}은
                 * - DataContext 객체의 PropertyName 속성을 참조합니다
                 * 
                 * 예시:
                 * XAML: <TextBlock Text="{Binding DeviceName}" />
                 * → DataContext(viewModel)의 DeviceName 속성 값을 표시
                 * 
                 * Python과 비교:
                 * - Python GUI 프레임워크에서는 보통 컨트롤에 직접 데이터 설정
                 * - C#에서는 DataContext를 통한 자동 바인딩으로 더 선언적
                 */
                DataContext = viewModel
            };

            /* ===== ShowDialog<T> 메서드 =====
             * ShowDialog는 모달 다이얼로그를 표시하고 결과를 반환합니다.
             * 
             * 제네릭 타입 <bool?>:
             * - 다이얼로그가 반환할 타입을 지정
             * - bool?: nullable bool (true, false, null 가능)
             * - true: 확인/성공, false: 취소/실패, null: 창 닫기(X 버튼 등)
             * 
             * await:
             * - 사용자가 다이얼로그를 닫을 때까지 대기
             * - 모달 다이얼로그이므로 백그라운드 UI는 비활성화됨
             * 
             * Python과 비교:
             * - PyQt: dialog.exec_() 메서드 (블로킹)
             * - Tkinter: wait_window(dialog) 메서드
             * - C#: await dialog.ShowDialog<T>() (비동기, non-blocking)
             * 
             * C#의 장점:
             * - async/await 덕분에 UI 스레드를 차단하지 않음
             * - 다이얼로그가 열려있어도 애플리케이션은 반응 가능
             */
            // 다이얼로그를 표시하고 사용자의 응답을 기다림 (await)
            bool? result = await dialog.ShowDialog<bool?>(_ownerWindow);
            // _ownerWindow: 부모 창 (다이얼로그가 이 창의 중앙에 표시됨)

            /* ===== bool? (Nullable Boolean) 비교 =====
             * bool?는 true, false, null 세 가지 값을 가질 수 있습니다.
             * 
             * result == true:
             * - result가 정확히 true인 경우만 true
             * - result가 false 또는 null이면 false
             * 
             * Python과 비교:
             * - Python: result is True (또는 result == True)
             * - C#: result == true
             * 
             * 주의:
             * - if (result) 만 쓰면 컴파일 오류! (bool?는 조건식에 직접 사용 불가)
             * - if (result == true) 또는 if (result.HasValue && result.Value) 사용
             */
            // 사용자가 '확인'을 누른 경우
            if (result == true)
            {
                /* ===== LINQ Count 메서드 (조건 포함) =====
                 * Count(predicate)는 조건을 만족하는 요소의 개수를 반환합니다.
                 * 
                 * Python과 비교:
                 * - Python: sum(1 for d in devices if d.connected)
                 * - Python: len([d for d in devices if d.connected])
                 * - C#: devices.Count(d => d.Connected)
                 * 
                 * Count() vs Count:
                 * - .Count(): LINQ 메서드 (모든 IEnumerable에서 사용 가능)
                 * - .Count: 속성 (List, Array 등에서 사용, 더 빠름)
                 */
                var reconnectedCount = disconnectedDevices.Count(d => d.Connected);
                // 재연결에 성공한 장치의 개수를 세기
                StatusMessage = $"{reconnectedCount}개 장치가 재연결되었습니다.";
            }
            else // 사용자가 '취소'를 누르거나 창을 닫은 경우
            {
                StatusMessage = "재연결이 취소되었습니다.";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"재연결 오류: {ex.Message}";
        }
        finally
        {
            // COHN 방식에서는 Health Check 타이머를 사용하지 않습니다
            // 기존 BLE 방식의 타이머 재시작 코드 (주석 처리)
            // _connectionHealthTimer?.Start();
        }
    }

    /* ===== Dispose 패턴 (리소스 정리) =====
     * Dispose 메서드는 객체가 사용한 리소스를 정리합니다.
     * 
     * Python과 비교:
     * - Python: __del__ 메서드 (소멸자, 자동 호출 타이밍 불확실)
     * - Python: __enter__/__exit__ (with 문의 context manager)
     * - C#: Dispose() 메서드 (IDisposable 인터페이스)
     * 
     * Python 예시:
     * class ViewModel:
     *     def __del__(self):
     *         self.timer.stop()
     *         # 하지만 __del__이 언제 호출될지 보장되지 않음
     * 
     *     # 또는 context manager 사용
     *     def __enter__(self):
     *         return self
     *     
     *     def __exit__(self, exc_type, exc_val, exc_tb):
     *         self.timer.stop()
     * 
     * # 사용: with ViewModel() as vm:
     * 
     * C# 예시:
     * public void Dispose()
     * {
     *     // 리소스 정리
     * }
     * 
     * // 사용: using (var vm = new ViewModel()) { ... }
     * // 또는 명시적 호출: vm.Dispose();
     * 
     * Dispose가 필요한 이유:
     * - 타이머, 파일 핸들, 네트워크 연결 등은 자동으로 정리되지 않음
     * - 명시적으로 정리하지 않으면 리소스 누수 발생
     * - C#의 가비지 컬렉터는 메모리만 관리 (타이머, 파일 등은 수동 정리 필요)
     */
    
    /// <summary>
    /// Cleanup resources
    /// 리소스를 정리합니다 (메모리 누수 방지)
    /// </summary>
    public void Dispose()
    {
        // COHN 방식에서는 타이머를 사용하지 않으므로 정리할 리소스가 없습니다
        // 기존 BLE 방식의 타이머 정리 코드 (주석 처리)
        // _connectionHealthTimer?.Stop();
        // _connectionHealthTimer?.Dispose();
    }
}

/* ===== 파일 끝 =====
 * 이제 여러분은 다음 개념들을 학습하셨습니다:
 * 
 * 1. C# 기본 문법: using, namespace, class, 접근 제한자
 * 2. MVVM 패턴: ViewModel, ObservableProperty, RelayCommand, DataBinding
 * 3. 비동기 프로그래밍: async, await, Task
 * 4. LINQ: Where, Select, FirstOrDefault, Any, Count, ToList
 * 5. 이벤트와 델리게이트: Timer.Elapsed, 람다식
 * 6. UI 스레드 관리: Dispatcher.UIThread.InvokeAsync
 * 7. 예외 처리: try-catch-finally
 * 8. Nullable 타입: ?, null 조건 연산자 (?., ??, !)
 * 9. 리소스 관리: Dispose 패턴
 * 10. 컬렉션: List<T>, ObservableCollection<T>
 * 
 * Python과의 주요 차이점:
 * - C#은 정적 타입 언어 (타입을 명시해야 함)
 * - C#은 중괄호 {}로 블록 구분 (Python은 들여쓰기)
 * - C#은 세미콜론 ; 필수 (Python은 줄바꿈)
 * - C#은 명시적 접근 제한자 (public, private 등)
 * - C#은 강력한 컴파일 시점 검사 (많은 오류를 미리 발견)
 * 
 * 다음 학습 추천:
 * 1. GoProDevice 모델 클래스 보기 (데이터 구조 이해)
 * 2. ApiService 클래스 보기 (API 통신 로직)
 * 3. GoProControlView.axaml 보기 (XAML UI 정의)
 * 4. 다른 ViewModel 클래스들 보기 (패턴 반복 확인)
 */

