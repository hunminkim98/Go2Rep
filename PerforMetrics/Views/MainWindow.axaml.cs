using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Platform;
using Avalonia.Threading;
using PerforMetrics.ViewModels;

namespace PerforMetrics.Views;

public partial class MainWindow : Window
{
    private bool _isInitializing = true;

    public MainWindow()
    {
        InitializeComponent();
        
        // Subscribe to DataContext changes
        DataContextChanged += OnDataContextChanged;
        
        // Subscribe to actual size changes
        PropertyChanged += OnWindowPropertyChanged;
    }

    private void OnDataContextChanged(object? sender, EventArgs e)
    {
        if (DataContext is MainWindowViewModel viewModel)
        {
            // Subscribe to property changes
            viewModel.PropertyChanged += OnViewModelPropertyChanged;
        }
        
        _isInitializing = false;
    }

    private void OnViewModelPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        // When window size properties change in ViewModel, wait for actual resize then center
        if (!_isInitializing && (e.PropertyName == nameof(MainWindowViewModel.WindowWidth) || 
                                  e.PropertyName == nameof(MainWindowViewModel.WindowHeight)))
        {
            // Use a small delay to ensure the window has actually resized
            _ = Task.Run(async () =>
            {
                await Task.Delay(50); // Wait for window to actually resize
                
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    CenterWindowOnScreen();
                });
            });
        }
    }

    private void OnWindowPropertyChanged(object? sender, AvaloniaPropertyChangedEventArgs e)
    {
        // Also react to actual Bounds changes
        if (e.Property == BoundsProperty && !_isInitializing)
        {
            CenterWindowOnScreen();
        }
    }

    private void CenterWindowOnScreen()
    {
        try
        {
            // Get the screen that contains the window
            var screen = Screens.ScreenFromWindow(this);
            
            if (screen != null)
            {
                var screenBounds = screen.WorkingArea;
                var windowWidth = Bounds.Width;
                var windowHeight = Bounds.Height;
                
                // Calculate center position
                var x = (screenBounds.Width - windowWidth) / 2 + screenBounds.X;
                var y = (screenBounds.Height - windowHeight) / 2 + screenBounds.Y;
                
                // Set window position
                Position = new PixelPoint((int)x, (int)y);
                
                // Console.WriteLine($"Centered window: Size={windowWidth}x{windowHeight}, Position={Position}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to center window: {ex.Message}");
        }
    }
}
