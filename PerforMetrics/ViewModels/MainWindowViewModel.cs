using System;
using Avalonia.Controls;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using PerforMetrics.Views;

namespace PerforMetrics.ViewModels;

/// <summary>
/// ViewModel for the Main Window
/// </summary>
public partial class MainWindowViewModel : ViewModelBase
{
    [ObservableProperty]
    private object? _currentView;

    [ObservableProperty]
    private double _windowWidth = 450;

    [ObservableProperty]
    private double _windowHeight = 400;

    private readonly SplashScreenViewModel _splashScreenViewModel;
    private readonly LandingPageViewModel _landingPageViewModel;

    public MainWindowViewModel()
    {
        // Initialize ViewModels
        _splashScreenViewModel = new SplashScreenViewModel();
        _landingPageViewModel = new LandingPageViewModel();

        // Subscribe to splash screen completion
        _splashScreenViewModel.LoadingCompleted += OnSplashScreenCompleted;

        // Start with splash screen (small window)
        WindowWidth = 450;
        WindowHeight = 400;
        
        CurrentView = new SplashScreen
        {
            DataContext = _splashScreenViewModel
        };
    }

    /// <summary>
    /// Handle splash screen completion
    /// </summary>
    private void OnSplashScreenCompleted(object? sender, EventArgs e)
    {
        // Switch to landing page on UI thread
        Dispatcher.UIThread.Post(() =>
        {
            // Expand window size for landing page
            WindowWidth = 1440;
            WindowHeight = 850;
            
            CurrentView = new LandingPage
            {
                DataContext = _landingPageViewModel
            };
        });
    }
}
