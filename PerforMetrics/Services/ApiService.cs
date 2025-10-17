using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
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

    public ApiService(string baseUrl = "http://localhost:8000")
    {
        _baseUrl = baseUrl;
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(_baseUrl),
            Timeout = TimeSpan.FromSeconds(30)
        };
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
            var response = await _httpClient.GetAsync("/api/gopro/ble/scan");
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
    /// Connect to a specific GoPro camera
    /// </summary>
    /// <param name="identifier">Last 4 digits of GoPro serial</param>
    /// <returns>True if connection successful</returns>
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
    /// Start or stop recording on GoPro cameras
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
            var response = await _httpClient.PostAsJsonAsync("/api/gopro/ble/recording", request);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Change GoPro settings
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
            var response = await _httpClient.PostAsJsonAsync("/api/gopro/ble/settings", request);
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
}

