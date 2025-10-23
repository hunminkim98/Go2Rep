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

    [ObservableProperty]
    private object? _currentContentView;

    // Singleton instances for view models to persist state across navigation
    private GoProControlViewModel? _goProControlViewModel;

    public ObservableCollection<string> ProjectOptions { get; }

    public LandingPageViewModel()
    {
        _apiService = new ApiService();
        
        // Initialize project options
        ProjectOptions = new ObservableCollection<string>
        {
            "No options available"
        };
        
        // Set Dashboard as default selected menu item
        SelectedMenuItem = "Dashboard";
        
        // Setup periodic health check
        _healthCheckTimer = new Timer(30000); // Check every 30 seconds (백엔드 로그 감소)
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
    /// Navigate to Dashboard (home page)
    /// </summary>
    [RelayCommand]
    private void NavigateToDashboard()
    {
        SelectedMenuItem = "Dashboard";
        CurrentContentView = null; // Reset to home view
    }

    /// <summary>
    /// Navigate to GoPro Control page
    /// </summary>
    [RelayCommand]
    private void NavigateToGoProControl()
    {
        SelectedMenuItem = "GoProControl";
        
        // Use singleton pattern to maintain connection state across navigation
        if (_goProControlViewModel == null)
        {
            _goProControlViewModel = new GoProControlViewModel();
            
            // Try to get the main window for dialog owner
            try
            {
                var mainWindow = Avalonia.Application.Current?.ApplicationLifetime 
                    is Avalonia.Controls.ApplicationLifetimes.IClassicDesktopStyleApplicationLifetime desktop
                    ? desktop.MainWindow
                    : null;
                
                if (mainWindow != null)
                {
                    _goProControlViewModel.SetOwnerWindow(mainWindow);
                }
            }
            catch
            {
                // Ignore if can't get window reference
            }
        }
        
        CurrentContentView = new Views.GoProControlView
        {
            DataContext = _goProControlViewModel
        };
    }

    /// <summary>
    /// Navigate to Synchronization page
    /// </summary>
    [RelayCommand]
    private void NavigateToSynchronization()
    {
        SelectedMenuItem = "Synchronization";
        CurrentContentView = null; // Reset to home view for now
        // TODO: Implement Synchronization view
    }

    /// <summary>
    /// Navigate to Classification page
    /// </summary>
    [RelayCommand]
    private void NavigateToClassification()
    {
        SelectedMenuItem = "Classification";
        CurrentContentView = null; // Reset to home view for now
        // TODO: Implement Classification view
    }

    /// <summary>
    /// Navigate to Calibration page
    /// </summary>
    [RelayCommand]
    private void NavigateToCalibration()
    {
        SelectedMenuItem = "Calibration";
        CurrentContentView = null; // Reset to home view for now
        // TODO: Implement Calibration view
    }

    /// <summary>
    /// Navigate to Motion Analysis page
    /// </summary>
    [RelayCommand]
    private void NavigateToMotionAnalysis()
    {
        SelectedMenuItem = "MotionAnalysis";
        CurrentContentView = null; // Reset to home view for now
        // TODO: Implement Motion Analysis view
    }

    /// <summary>
    /// Navigate to Report Generator page
    /// </summary>
    [RelayCommand]
    private void NavigateToReportGenerator()
    {
        SelectedMenuItem = "ReportGenerator";
        CurrentContentView = null; // Reset to home view for now
        // TODO: Implement Report Generator view
    }

    /// <summary>
    /// Cleanup resources
    /// </summary>
    public void Dispose()
    {
        _healthCheckTimer?.Stop();
        _healthCheckTimer?.Dispose();
        _goProControlViewModel?.Dispose();
    }
}

