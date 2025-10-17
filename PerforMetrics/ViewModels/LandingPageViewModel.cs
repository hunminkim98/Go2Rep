using System;
using System.Threading.Tasks;
using System.Timers;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PerforMetrics.Services;

namespace PerforMetrics.ViewModels;

/// <summary>
/// ViewModel for the Landing Page
/// </summary>
public partial class LandingPageViewModel : ViewModelBase
{
    private readonly ApiService _apiService;
    private readonly Timer _healthCheckTimer;

    [ObservableProperty]
    private bool _isBackendConnected;

    [ObservableProperty]
    private string _backendStatus = "Checking...";

    [ObservableProperty]
    private string _versionInfo = "v1.0.0";

    public LandingPageViewModel()
    {
        _apiService = new ApiService();
        
        // Setup periodic health check
        _healthCheckTimer = new Timer(5000); // Check every 5 seconds
        _healthCheckTimer.Elapsed += async (sender, e) => await CheckBackendHealthAsync();
        _healthCheckTimer.Start();
        
        // Initial health check
        _ = CheckBackendHealthAsync();
    }

    /// <summary>
    /// Check backend health status
    /// </summary>
    private async Task CheckBackendHealthAsync()
    {
        try
        {
            IsBackendConnected = await _apiService.CheckBackendHealthAsync();
            BackendStatus = IsBackendConnected ? "Connected" : "Disconnected";
        }
        catch
        {
            IsBackendConnected = false;
            BackendStatus = "Disconnected";
        }
    }

    /// <summary>
    /// Navigate to GoPro Control page
    /// </summary>
    [RelayCommand]
    private void NavigateToGoProControl()
    {
        // TODO: Implement navigation to GoPro Control page
        Console.WriteLine("Navigate to GoPro Control");
    }

    /// <summary>
    /// Navigate to Synchronization page
    /// </summary>
    [RelayCommand]
    private void NavigateToSynchronization()
    {
        // TODO: Implement navigation to Synchronization page
        Console.WriteLine("Navigate to Synchronization");
    }

    /// <summary>
    /// Navigate to Classification page
    /// </summary>
    [RelayCommand]
    private void NavigateToClassification()
    {
        // TODO: Implement navigation to Classification page
        Console.WriteLine("Navigate to Classification");
    }

    /// <summary>
    /// Navigate to Calibration page
    /// </summary>
    [RelayCommand]
    private void NavigateToCalibration()
    {
        // TODO: Implement navigation to Calibration page
        Console.WriteLine("Navigate to Calibration");
    }

    /// <summary>
    /// Navigate to Motion Analysis page
    /// </summary>
    [RelayCommand]
    private void NavigateToMotionAnalysis()
    {
        // TODO: Implement navigation to Motion Analysis page
        Console.WriteLine("Navigate to Motion Analysis");
    }

    /// <summary>
    /// Navigate to Report Generator page
    /// </summary>
    [RelayCommand]
    private void NavigateToReportGenerator()
    {
        // TODO: Implement navigation to Report Generator page
        Console.WriteLine("Navigate to Report Generator");
    }

    /// <summary>
    /// Cleanup resources
    /// </summary>
    public void Dispose()
    {
        _healthCheckTimer?.Stop();
        _healthCheckTimer?.Dispose();
    }
}

