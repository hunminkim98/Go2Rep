using Avalonia.Controls;
using Avalonia.Interactivity;
using PerforMetrics.ViewModels;

namespace PerforMetrics.Views;

public partial class WiFiProvisionDialog : Window
{
    public WiFiProvisionDialog()
    {
        InitializeComponent();
    }

    private void ConfirmButton_Click(object? sender, RoutedEventArgs e)
    {
        if (DataContext is WiFiProvisionDialogViewModel viewModel)
        {
            if (viewModel.ValidateInput())
            {
                Close(true); // Return true on success
            }
        }
    }

    private void CancelButton_Click(object? sender, RoutedEventArgs e)
    {
        Close(false); // Return false on cancel
    }
}

