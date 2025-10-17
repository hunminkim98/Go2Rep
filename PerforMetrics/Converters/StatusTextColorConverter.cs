using System;
using System.Globalization;
using Avalonia.Data.Converters;
using Avalonia.Media;

namespace PerforMetrics.Converters;

/// <summary>
/// Converts boolean connection status to text color
/// </summary>
public class StatusTextColorConverter : IValueConverter
{
    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        if (value is bool isConnected)
        {
            return new SolidColorBrush(isConnected ? Colors.LimeGreen : Colors.OrangeRed);
        }
        return new SolidColorBrush(Colors.Gray);
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}

