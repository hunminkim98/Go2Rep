using System;
using System.Collections.ObjectModel;
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

    [ObservableProperty]
    private bool _isSidebarVisible = true;

    [ObservableProperty]
    private string _selectedMenuItem = "";

    [ObservableProperty]
    private string _selectedProject = "No options available";

    [ObservableProperty]
    private string _mainContentMessage = "DepthAI connected, awaiting device...";

    public ObservableCollection<string> ProjectOptions { get; }

    public LandingPageViewModel()
    {
        _apiService = new ApiService();
        
        // Initialize project options
        ProjectOptions = new ObservableCollection<string>
        {
            "No options available"
        };
        
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
            BackendStatus = IsBackendConnected ? "Backend Connected" : "Backend Disconnected";
            MainContentMessage = IsBackendConnected 
                ? "Backend connected, awaiting device..." 
                : "Backend disconnected. Please start the backend service.";
        }
        catch
        {
            IsBackendConnected = false;
            BackendStatus = "Backend Disconnected";
            MainContentMessage = "Backend disconnected. Please start the backend service.";
        }
    }

    /// <summary>
    /// Toggle sidebar visibility
    /// </summary>
    [RelayCommand]
    private void ToggleSidebar()
    {
        IsSidebarVisible = !IsSidebarVisible;
    }

    /// <summary>
    /// Navigate to GoPro Control page
    /// </summary>
    [RelayCommand]
    private void NavigateToGoProControl()
    {
        SelectedMenuItem = "GoProControl";
        // TODO: Implement navigation to GoPro Control page
        Console.WriteLine("Navigate to GoPro Control");
    }

    /// <summary>
    /// Navigate to Synchronization page
    /// </summary>
    [RelayCommand]
    private void NavigateToSynchronization()
    {
        SelectedMenuItem = "Synchronization";
        // TODO: Implement navigation to Synchronization page
        Console.WriteLine("Navigate to Synchronization");
    }

    /// <summary>
    /// Navigate to Classification page
    /// </summary>
    [RelayCommand]
    private void NavigateToClassification()
    {
        SelectedMenuItem = "Classification";
        // TODO: Implement navigation to Classification page
        Console.WriteLine("Navigate to Classification");
    }

    /// <summary>
    /// Navigate to Calibration page
    /// </summary>
    [RelayCommand]
    private void NavigateToCalibration()
    {
        SelectedMenuItem = "Calibration";
        // TODO: Implement navigation to Calibration page
        Console.WriteLine("Navigate to Calibration");
    }

    /// <summary>
    /// Navigate to Motion Analysis page
    /// </summary>
    [RelayCommand]
    private void NavigateToMotionAnalysis()
    {
        SelectedMenuItem = "MotionAnalysis";
        // TODO: Implement navigation to Motion Analysis page
        Console.WriteLine("Navigate to Motion Analysis");
    }

    /// <summary>
    /// Navigate to Report Generator page
    /// </summary>
    [RelayCommand]
    private void NavigateToReportGenerator()
    {
        SelectedMenuItem = "ReportGenerator";
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

