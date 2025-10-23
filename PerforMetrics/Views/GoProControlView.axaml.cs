using Avalonia.Controls;
using PerforMetrics.ViewModels;

namespace PerforMetrics.Views;

public partial class GoProControlView : UserControl
{
    public GoProControlView()
    {
        InitializeComponent();
        DataContext = new GoProControlViewModel();
    }
}

