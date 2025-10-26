namespace PerforMetrics.Models;

/// <summary>
/// WiFi Settings Model
/// WiFi 설정 모델
/// </summary>
public class WiFiSettings
{
    /// <summary>
    /// WiFi SSID (Network Name)
    /// WiFi SSID (네트워크 이름)
    /// </summary>
    public string Ssid { get; set; } = "";

    /// <summary>
    /// WiFi Password
    /// WiFi 비밀번호
    /// </summary>
    public string Password { get; set; } = "";

    /// <summary>
    /// Check if WiFi settings are configured
    /// WiFi 설정이 구성되어 있는지 확인
    /// </summary>
    public bool IsConfigured => !string.IsNullOrWhiteSpace(Ssid) && !string.IsNullOrWhiteSpace(Password);
}

