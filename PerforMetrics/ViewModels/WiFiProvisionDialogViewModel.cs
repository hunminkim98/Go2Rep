using System;
using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PerforMetrics.Models;

namespace PerforMetrics.ViewModels;

/// <summary>
/// ViewModel for WiFi Provisioning Dialog
/// WiFi 프로비저닝 다이얼로그의 ViewModel
/// </summary>
public partial class WiFiProvisionDialogViewModel : ViewModelBase
{
    [ObservableProperty]
    private string _ssid = "";

    [ObservableProperty]
    private string _password = "";

    [ObservableProperty]
    private string _errorMessage = "";

    [ObservableProperty]
    private bool _hasError;

    [ObservableProperty]
    private string _dialogTitle = "";

    [ObservableProperty]
    private ObservableCollection<WiFiProfile> _wiFiProfiles = new();

    [ObservableProperty]
    private WiFiProfile? _selectedProfile;

    public string GoProIdentifier { get; set; } = "";

    public bool IsGlobalMode { get; set; } = false;

    /// <summary>
    /// Constructor for device-specific WiFi provisioning
    /// 장치별 WiFi 프로비저닝용 생성자
    /// </summary>
    public WiFiProvisionDialogViewModel(string identifier)
    {
        GoProIdentifier = identifier;
        IsGlobalMode = false;
        DialogTitle = $"GoPro {identifier}을(를) WiFi로 연결합니다";
    }

    /// <summary>
    /// Constructor for global WiFi settings
    /// 전역 WiFi 설정용 생성자
    /// </summary>
    public WiFiProvisionDialogViewModel()
    {
        GoProIdentifier = "";
        IsGlobalMode = true;
        DialogTitle = "전역 WiFi 설정";
    }

    /// <summary>
    /// Constructor with pre-filled settings (for editing)
    /// 기존 설정으로 초기화하는 생성자 (편집용)
    /// </summary>
    public WiFiProvisionDialogViewModel(string ssid, string password)
    {
        GoProIdentifier = "";
        IsGlobalMode = true;
        DialogTitle = "전역 WiFi 설정";
        Ssid = ssid;
        Password = password;
    }

    /// <summary>
    /// Load WiFi profiles into the list
    /// WiFi 프로필 목록 로드
    /// </summary>
    public void LoadProfiles(ObservableCollection<WiFiProfile> profiles)
    {
        WiFiProfiles = profiles;
    }

    /// <summary>
    /// Handle profile selection change
    /// 프로필 선택 변경 처리
    /// </summary>
    partial void OnSelectedProfileChanged(WiFiProfile? value)
    {
        if (value != null)
        {
            Ssid = value.Ssid;
            Password = value.Password;
            ErrorMessage = "";
            HasError = false;
        }
    }

    /// <summary>
    /// Validate input fields
    /// 입력 필드 유효성 검증
    /// </summary>
    public bool ValidateInput()
    {
        if (string.IsNullOrWhiteSpace(Ssid))
        {
            ErrorMessage = "WiFi SSID를 입력해주세요.";
            HasError = true;
            return false;
        }

        if (string.IsNullOrWhiteSpace(Password))
        {
            ErrorMessage = "WiFi 비밀번호를 입력해주세요.";
            HasError = true;
            return false;
        }

        if (Password.Length < 8)
        {
            ErrorMessage = "WiFi 비밀번호는 최소 8자 이상이어야 합니다.";
            HasError = true;
            return false;
        }

        ErrorMessage = "";
        HasError = false;
        return true;
    }
}

