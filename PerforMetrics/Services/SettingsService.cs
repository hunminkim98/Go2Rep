using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using PerforMetrics.Models;

namespace PerforMetrics.Services;

/// <summary>
/// Service for managing application settings
/// 애플리케이션 설정 관리 서비스
/// </summary>
public class SettingsService
{
    private const string SettingsFileName = "appsettings.json";
    private const int MaxProfileCount = 10;
    private readonly string _settingsFilePath;

    public SettingsService()
    {
        // Get the path to appsettings.json in the application directory
        _settingsFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, SettingsFileName);
    }

    /// <summary>
    /// Get the current settings file path (for debugging)
    /// 현재 설정 파일 경로 가져오기 (디버깅용)
    /// </summary>
    public string GetSettingsFilePath() => _settingsFilePath;

    /// <summary>
    /// Load WiFi settings from appsettings.json
    /// appsettings.json에서 WiFi 설정 로드
    /// </summary>
    public async Task<WiFiSettings> LoadWiFiSettingsAsync()
    {
        try
        {
            if (!File.Exists(_settingsFilePath))
            {
                return new WiFiSettings();
            }

            var json = await File.ReadAllTextAsync(_settingsFilePath);
            var jsonDoc = JsonDocument.Parse(json);

            if (jsonDoc.RootElement.TryGetProperty("WiFiSettings", out var wifiElement))
            {
                var ssid = wifiElement.TryGetProperty("Ssid", out var ssidElement) 
                    ? ssidElement.GetString() ?? "" 
                    : "";
                var password = wifiElement.TryGetProperty("Password", out var passwordElement) 
                    ? passwordElement.GetString() ?? "" 
                    : "";

                return new WiFiSettings { Ssid = ssid, Password = password };
            }

            return new WiFiSettings();
        }
        catch (Exception)
        {
            // If any error occurs, return empty settings
            return new WiFiSettings();
        }
    }

    /// <summary>
    /// Save WiFi settings to appsettings.json
    /// appsettings.json에 WiFi 설정 저장
    /// </summary>
    public async Task<(bool Success, string ErrorMessage)> SaveWiFiSettingsAsync(WiFiSettings settings)
    {
        try
        {
            if (!File.Exists(_settingsFilePath))
            {
                return (false, $"설정 파일을 찾을 수 없습니다: {_settingsFilePath}");
            }

            var json = await File.ReadAllTextAsync(_settingsFilePath);
            var jsonDoc = JsonDocument.Parse(json);
            var root = jsonDoc.RootElement;

            // Build new JSON with updated WiFi settings
            using var stream = new MemoryStream();
            using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true }))
            {
                writer.WriteStartObject();

                // Copy all existing properties
                foreach (var property in root.EnumerateObject())
                {
                    if (property.Name == "WiFiSettings")
                    {
                        // Write updated WiFi settings
                        writer.WritePropertyName("WiFiSettings");
                        writer.WriteStartObject();
                        writer.WriteString("Ssid", settings.Ssid);
                        writer.WriteString("Password", settings.Password);
                        writer.WriteEndObject();
                    }
                    else
                    {
                        // Copy existing property as-is
                        property.WriteTo(writer);
                    }
                }

                // If WiFiSettings didn't exist, add it
                if (!root.TryGetProperty("WiFiSettings", out _))
                {
                    writer.WritePropertyName("WiFiSettings");
                    writer.WriteStartObject();
                    writer.WriteString("Ssid", settings.Ssid);
                    writer.WriteString("Password", settings.Password);
                    writer.WriteEndObject();
                }

                writer.WriteEndObject();
            }

            // Write to file
            var updatedJson = System.Text.Encoding.UTF8.GetString(stream.ToArray());
            await File.WriteAllTextAsync(_settingsFilePath, updatedJson);

            return (true, "");
        }
        catch (Exception ex)
        {
            return (false, $"저장 오류: {ex.Message}");
        }
    }

    /// <summary>
    /// Load all WiFi profiles from appsettings.json
    /// appsettings.json에서 모든 WiFi 프로필 로드
    /// </summary>
    public async Task<List<WiFiProfile>> LoadWiFiProfilesAsync()
    {
        try
        {
            if (!File.Exists(_settingsFilePath))
            {
                return new List<WiFiProfile>();
            }

            var json = await File.ReadAllTextAsync(_settingsFilePath);
            var jsonDoc = JsonDocument.Parse(json);

            if (jsonDoc.RootElement.TryGetProperty("WiFiProfiles", out var profilesElement))
            {
                var profiles = new List<WiFiProfile>();
                
                foreach (var profileElement in profilesElement.EnumerateArray())
                {
                    var profile = new WiFiProfile
                    {
                        Id = profileElement.TryGetProperty("Id", out var idElement) 
                            ? idElement.GetString() ?? Guid.NewGuid().ToString() 
                            : Guid.NewGuid().ToString(),
                        Ssid = profileElement.TryGetProperty("Ssid", out var ssidElement) 
                            ? ssidElement.GetString() ?? "" 
                            : "",
                        Password = profileElement.TryGetProperty("Password", out var passwordElement) 
                            ? passwordElement.GetString() ?? "" 
                            : "",
                        LastUsed = profileElement.TryGetProperty("LastUsed", out var lastUsedElement) 
                            && DateTime.TryParse(lastUsedElement.GetString(), out var parsedDate)
                            ? parsedDate 
                            : DateTime.Now
                    };
                    
                    if (profile.IsValid)
                    {
                        profiles.Add(profile);
                    }
                }
                
                // Sort by LastUsed descending (most recent first)
                return profiles.OrderByDescending(p => p.LastUsed).ToList();
            }

            return new List<WiFiProfile>();
        }
        catch (Exception)
        {
            return new List<WiFiProfile>();
        }
    }

    /// <summary>
    /// Save or update a WiFi profile
    /// WiFi 프로필 저장 또는 업데이트
    /// </summary>
    public async Task<(bool Success, string ErrorMessage)> SaveWiFiProfileAsync(WiFiProfile profile)
    {
        try
        {
            if (!File.Exists(_settingsFilePath))
            {
                return (false, $"설정 파일을 찾을 수 없습니다: {_settingsFilePath}");
            }

            var json = await File.ReadAllTextAsync(_settingsFilePath);
            var jsonDoc = JsonDocument.Parse(json);
            var root = jsonDoc.RootElement;

            // Load existing profiles
            var profiles = await LoadWiFiProfilesAsync();
            
            // Check if profile with same SSID exists
            var existingProfile = profiles.FirstOrDefault(p => p.Ssid == profile.Ssid);
            if (existingProfile != null)
            {
                // Update existing profile
                existingProfile.Password = profile.Password;
                existingProfile.LastUsed = DateTime.Now;
            }
            else
            {
                // Add new profile
                profile.LastUsed = DateTime.Now;
                profiles.Add(profile);
            }
            
            // Keep only the 10 most recent profiles
            profiles = profiles.OrderByDescending(p => p.LastUsed).Take(MaxProfileCount).ToList();

            // Build new JSON
            using var stream = new MemoryStream();
            using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true }))
            {
                writer.WriteStartObject();

                // Copy existing properties
                foreach (var property in root.EnumerateObject())
                {
                    if (property.Name == "WiFiProfiles")
                    {
                        // Write updated profiles
                        writer.WritePropertyName("WiFiProfiles");
                        writer.WriteStartArray();
                        foreach (var p in profiles)
                        {
                            writer.WriteStartObject();
                            writer.WriteString("Id", p.Id);
                            writer.WriteString("Ssid", p.Ssid);
                            writer.WriteString("Password", p.Password);
                            writer.WriteString("LastUsed", p.LastUsed.ToString("O"));
                            writer.WriteEndObject();
                        }
                        writer.WriteEndArray();
                    }
                    else if (property.Name == "WiFiSettings")
                    {
                        // Update current WiFiSettings with most recent profile
                        var mostRecent = profiles.First();
                        writer.WritePropertyName("WiFiSettings");
                        writer.WriteStartObject();
                        writer.WriteString("Ssid", mostRecent.Ssid);
                        writer.WriteString("Password", mostRecent.Password);
                        writer.WriteEndObject();
                    }
                    else
                    {
                        property.WriteTo(writer);
                    }
                }

                // Add WiFiProfiles if it didn't exist
                if (!root.TryGetProperty("WiFiProfiles", out _))
                {
                    writer.WritePropertyName("WiFiProfiles");
                    writer.WriteStartArray();
                    foreach (var p in profiles)
                    {
                        writer.WriteStartObject();
                        writer.WriteString("Id", p.Id);
                        writer.WriteString("Ssid", p.Ssid);
                        writer.WriteString("Password", p.Password);
                        writer.WriteString("LastUsed", p.LastUsed.ToString("O"));
                        writer.WriteEndObject();
                    }
                    writer.WriteEndArray();
                }

                writer.WriteEndObject();
            }

            // Write to file
            var updatedJson = System.Text.Encoding.UTF8.GetString(stream.ToArray());
            await File.WriteAllTextAsync(_settingsFilePath, updatedJson);

            return (true, "");
        }
        catch (Exception ex)
        {
            return (false, $"프로필 저장 오류: {ex.Message}");
        }
    }

    /// <summary>
    /// Delete a WiFi profile
    /// WiFi 프로필 삭제
    /// </summary>
    public async Task<(bool Success, string ErrorMessage)> DeleteWiFiProfileAsync(string profileId)
    {
        try
        {
            if (!File.Exists(_settingsFilePath))
            {
                return (false, $"설정 파일을 찾을 수 없습니다: {_settingsFilePath}");
            }

            var json = await File.ReadAllTextAsync(_settingsFilePath);
            var jsonDoc = JsonDocument.Parse(json);
            var root = jsonDoc.RootElement;

            // Load existing profiles
            var profiles = await LoadWiFiProfilesAsync();
            
            // Remove the specified profile
            profiles = profiles.Where(p => p.Id != profileId).ToList();
            
            if (profiles.Count == 0)
            {
                // No profiles left, clear WiFiSettings too
                return await ClearAllProfilesAsync();
            }

            // Build new JSON
            using var stream = new MemoryStream();
            using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true }))
            {
                writer.WriteStartObject();

                foreach (var property in root.EnumerateObject())
                {
                    if (property.Name == "WiFiProfiles")
                    {
                        writer.WritePropertyName("WiFiProfiles");
                        writer.WriteStartArray();
                        foreach (var p in profiles)
                        {
                            writer.WriteStartObject();
                            writer.WriteString("Id", p.Id);
                            writer.WriteString("Ssid", p.Ssid);
                            writer.WriteString("Password", p.Password);
                            writer.WriteString("LastUsed", p.LastUsed.ToString("O"));
                            writer.WriteEndObject();
                        }
                        writer.WriteEndArray();
                    }
                    else if (property.Name == "WiFiSettings")
                    {
                        // Update with most recent remaining profile
                        var mostRecent = profiles.OrderByDescending(p => p.LastUsed).First();
                        writer.WritePropertyName("WiFiSettings");
                        writer.WriteStartObject();
                        writer.WriteString("Ssid", mostRecent.Ssid);
                        writer.WriteString("Password", mostRecent.Password);
                        writer.WriteEndObject();
                    }
                    else
                    {
                        property.WriteTo(writer);
                    }
                }

                writer.WriteEndObject();
            }

            var updatedJson = System.Text.Encoding.UTF8.GetString(stream.ToArray());
            await File.WriteAllTextAsync(_settingsFilePath, updatedJson);

            return (true, "");
        }
        catch (Exception ex)
        {
            return (false, $"프로필 삭제 오류: {ex.Message}");
        }
    }

    /// <summary>
    /// Clear all WiFi profiles
    /// 모든 WiFi 프로필 삭제
    /// </summary>
    private async Task<(bool Success, string ErrorMessage)> ClearAllProfilesAsync()
    {
        var emptySettings = new WiFiSettings { Ssid = "", Password = "" };
        return await SaveWiFiSettingsAsync(emptySettings);
    }
}

