using Avalonia.Controls;
using PerforMetrics.ViewModels;

namespace PerforMetrics.Views;

public partial class LandingPage : UserControl
{
    public LandingPage()
    {
        InitializeComponent();
        DataContext = new LandingPageViewModel();
    }
}

