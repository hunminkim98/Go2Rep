using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading.Tasks;
using PerforMetrics.Models;

namespace PerforMetrics.Services;

/// <summary>
/// Service for communicating with the Python FastAPI backend
/// </summary>
public class ApiService
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;

    public ApiService(string? baseUrl = null)
    {
        // Priority: 1) Parameter, 2) Environment variable, 3) appsettings.json, 4) Default
        if (string.IsNullOrEmpty(baseUrl))
        {
            // Try environment variable first (set by start_fullstack.py)
            var envUrl = Environment.GetEnvironmentVariable("BACKEND_URL");
            Console.WriteLine($"[ApiService] Environment BACKEND_URL: {envUrl ?? "null"}");
            
            baseUrl = envUrl;
            
            // If not in env, try reading from appsettings.json
            if (string.IsNullOrEmpty(baseUrl))
            {
                baseUrl = ReadBaseUrlFromSettings();
                Console.WriteLine($"[ApiService] Settings BaseUrl: {baseUrl ?? "null"}");
            }
            
            // Final fallback to default
            if (string.IsNullOrEmpty(baseUrl))
            {
                baseUrl = "http://localhost:8000";
                Console.WriteLine("[ApiService] Using default: http://localhost:8000");
            }
        }
        
        _baseUrl = baseUrl;
        Console.WriteLine($"[ApiService] Final BaseUrl: {_baseUrl}");
        
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(_baseUrl),
            Timeout = TimeSpan.FromSeconds(30)
        };
    }
    
    private static string? ReadBaseUrlFromSettings()
    {
        try
        {
            // Try multiple possible locations for appsettings.json
            var possiblePaths = new[]
            {
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "appsettings.json"),
                Path.Combine(Directory.GetCurrentDirectory(), "appsettings.json"),
                Path.Combine(Directory.GetCurrentDirectory(), "..", "appsettings.json"),
                Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "appsettings.json")
            };
            
            foreach (var settingsPath in possiblePaths)
            {
                if (File.Exists(settingsPath))
                {
                    var json = File.ReadAllText(settingsPath);
                    using var doc = JsonDocument.Parse(json);
                    
                    if (doc.RootElement.TryGetProperty("Backend", out var backend))
                    {
                        if (backend.TryGetProperty("BaseUrl", out var baseUrl))
                        {
                            var url = baseUrl.GetString();
                            if (!string.IsNullOrEmpty(url))
                            {
                                return url;
                            }
                        }
                    }
                }
            }
        }
        catch
        {
            // Ignore errors and continue to fallback
        }
        
        return null;
    }

    /// <summary>
    /// Check if backend is healthy and running
    /// </summary>
    /// <returns>True if backend is healthy, false otherwise</returns>
    public async Task<bool> CheckBackendHealthAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/health");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Get system information from backend
    /// </summary>
    /// <returns>System info dictionary or null if failed</returns>
    public async Task<Dictionary<string, object>?> GetSystemInfoAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/api/system/info");
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            }
            return null;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Scan for available GoPro cameras via BLE
    /// </summary>
    /// <returns>List of discovered GoPro devices</returns>
    public async Task<List<GoProDevice>?> ScanGoProDevicesAsync()
    {
        try
        {
            var url = $"{_baseUrl}/api/gopro/ble/scan";
            Console.WriteLine($"[ApiService] Scanning GoPro devices: {url}");
            
            var response = await _httpClient.GetAsync("/api/gopro/ble/scan");
            Console.WriteLine($"[ApiService] Response status: {response.StatusCode}");
            
            if (response.IsSuccessStatusCode)
            {
                var devices = await response.Content.ReadFromJsonAsync<List<GoProDevice>>();
                Console.WriteLine($"[ApiService] Found {devices?.Count ?? 0} devices");
                return devices;
            }
            Console.WriteLine($"[ApiService] Scan failed with status: {response.StatusCode}");
            return null;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ApiService] Scan error: {ex.Message}");
            return null;
        }
    }

    /// <summary>
    /// Get list of COHN-enabled devices
    /// </summary>
    /// <returns>List of COHN devices</returns>
    public async Task<List<GoProDevice>?> GetCOHNDevicesAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/api/gopro/cohn/devices");
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<List<GoProDevice>>();
            }
            return null;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Provision a specific GoPro camera for COHN
    /// </summary>
    /// <param name="identifier">Last 4 digits of GoPro serial</param>
    /// <param name="ssid">WiFi SSID</param>
    /// <param name="password">WiFi password</param>
    /// <returns>True if provisioning successful</returns>
    public async Task<bool> ProvisionGoProAsync(string identifier, string ssid, string password)
    {
        try
        {
            var request = new
            {
                identifier,
                ssid,
                password
            };
            var response = await _httpClient.PostAsJsonAsync("/api/gopro/cohn/provision", request);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Connect to a specific GoPro camera (legacy BLE method - deprecated)
    /// Use ProvisionGoProAsync for COHN instead
    /// </summary>
    /// <param name="identifier">Last 4 digits of GoPro serial</param>
    /// <returns>True if connection successful</returns>
    [Obsolete("Use ProvisionGoProAsync for COHN-based connection")]
    public async Task<bool> ConnectGoProAsync(string identifier)
    {
        try
        {
            var response = await _httpClient.PostAsync($"/api/gopro/ble/connect/{identifier}", null);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Start or stop recording on GoPro cameras via COHN
    /// </summary>
    /// <param name="action">start or stop</param>
    /// <param name="identifiers">Target identifiers, null for all</param>
    /// <returns>True if command sent successfully</returns>
    public async Task<bool> ControlRecordingAsync(string action, List<string>? identifiers = null)
    {
        try
        {
            var request = new
            {
                action,
                identifiers
            };
            var response = await _httpClient.PostAsJsonAsync("/api/gopro/cohn/recording", request);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Change GoPro settings via COHN
    /// </summary>
    /// <param name="fps">Frames per second (60, 120, 240)</param>
    /// <param name="resolution">Resolution (1080, 2700, 4000)</param>
    /// <param name="identifiers">Target identifiers, null for all</param>
    /// <returns>True if settings changed successfully</returns>
    public async Task<bool> ChangeSettingsAsync(int? fps = null, int? resolution = null, List<string>? identifiers = null)
    {
        try
        {
            var request = new
            {
                fps,
                resolution,
                identifiers
            };
            var response = await _httpClient.PostAsJsonAsync("/api/gopro/cohn/settings", request);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Power off a specific GoPro camera
    /// </summary>
    /// <param name="identifier">Last 4 digits of GoPro serial</param>
    /// <returns>True if power off command sent successfully</returns>
    public async Task<bool> PowerOffGoProAsync(string identifier)
    {
        try
        {
            var response = await _httpClient.PostAsync($"/api/gopro/ble/power-off/{identifier}", null);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Check if a specific GoPro device is still connected and responsive
    /// </summary>
    /// <param name="identifier">Last 4 digits of GoPro serial</param>
    /// <returns>True if device is connected and responsive</returns>
    public async Task<bool> CheckDeviceConnectionAsync(string identifier)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/api/gopro/health/{identifier}");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Attempt to reconnect to a specific GoPro device
    /// </summary>
    /// <param name="identifier">Last 4 digits of GoPro serial</param>
    /// <returns>True if reconnection successful</returns>
    public async Task<bool> ReconnectGoProAsync(string identifier)
    {
        try
        {
            var response = await _httpClient.PostAsync($"/api/gopro/reconnect/{identifier}", null);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }
}

