using System;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using PerforMetrics.Services;

namespace PerforMetrics.ViewModels;

/// <summary>
/// ViewModel for the Splash Screen
/// </summary>
public partial class SplashScreenViewModel : ViewModelBase
{
    private readonly ApiService _apiService;

    [ObservableProperty]
    private bool _isLoading = true;

    [ObservableProperty]
    private string _versionInfo = "v1.0.0";

    /// <summary>
    /// Event raised when loading is complete
    /// </summary>
    public event EventHandler? LoadingCompleted;

    public SplashScreenViewModel()
    {
        _apiService = new ApiService();
        
        // Start loading automatically
        _ = StartLoadingAsync();
    }

    /// <summary>
    /// Start the loading process
    /// </summary>
    private async Task StartLoadingAsync()
    {
        try
        {
            // Start timer to ensure minimum display time (3 seconds)
            var minDisplayTime = Task.Delay(3000);
            
            // Check backend health (but don't wait for it to succeed)
            var healthCheck = Task.Run(async () =>
            {
                try
                {
                    await _apiService.CheckBackendHealthAsync();
                }
                catch
                {
                    // Ignore errors - we'll continue even if backend is not ready
                }
            });

            // Wait for both tasks (minimum time is 3 seconds)
            await Task.WhenAll(minDisplayTime, healthCheck);

            // Mark loading as complete
            IsLoading = false;
            
            // Raise completion event
            LoadingCompleted?.Invoke(this, EventArgs.Empty);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Splash screen loading error: {ex.Message}");
            
            // Still complete even if there's an error
            IsLoading = false;
            LoadingCompleted?.Invoke(this, EventArgs.Empty);
        }
    }
}

