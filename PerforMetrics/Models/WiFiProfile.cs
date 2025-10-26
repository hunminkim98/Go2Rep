using System;

namespace PerforMetrics.Models;

/// <summary>
/// WiFi Profile Model
/// WiFi 프로필 모델 (과거 사용 이력 포함)
/// </summary>
public class WiFiProfile
{
    /// <summary>
    /// Unique identifier for the profile
    /// 프로필 고유 식별자
    /// </summary>
    public string Id { get; set; } = Guid.NewGuid().ToString();

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
    /// Last used timestamp
    /// 마지막 사용 시간
    /// </summary>
    public DateTime LastUsed { get; set; } = DateTime.Now;

    /// <summary>
    /// Check if profile is valid
    /// 프로필 유효성 확인
    /// </summary>
    public bool IsValid => !string.IsNullOrWhiteSpace(Ssid) && !string.IsNullOrWhiteSpace(Password);

    /// <summary>
    /// Display name for ComboBox
    /// ComboBox 표시용 이름
    /// </summary>
    public string DisplayName => $"{Ssid} (마지막 사용: {LastUsed:MM/dd HH:mm})";
}

