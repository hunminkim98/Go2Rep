using System;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

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

    public string GoProIdentifier { get; set; } = "";

    public WiFiProvisionDialogViewModel(string identifier)
    {
        GoProIdentifier = identifier;
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

