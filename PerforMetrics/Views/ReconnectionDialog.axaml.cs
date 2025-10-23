using Avalonia.Controls;
using PerforMetrics.ViewModels;

namespace PerforMetrics.Views;

/// <summary>
/// Dialog window for GoPro reconnection
/// </summary>
public partial class ReconnectionDialog : Window
{
    public ReconnectionDialog()
    {
        InitializeComponent();
        
        // Subscribe to close request from ViewModel
        DataContextChanged += OnDataContextChanged;
    }

    private void OnDataContextChanged(object? sender, System.EventArgs e)
    {
        if (DataContext is ReconnectionDialogViewModel viewModel)
        {
            viewModel.RequestClose += OnRequestClose;
        }
    }

    private void OnRequestClose(object? sender, bool success)
    {
        Close(success);
    }

    protected override void OnClosed(System.EventArgs e)
    {
        // Cleanup: unsubscribe from events
        if (DataContext is ReconnectionDialogViewModel viewModel)
        {
            viewModel.RequestClose -= OnRequestClose;
            viewModel.Dispose();
        }
        
        base.OnClosed(e);
    }
}


