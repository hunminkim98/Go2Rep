using System;
using System.Globalization;
using Avalonia.Data.Converters;
using Avalonia.Media;

namespace PerforMetrics.Converters;

/// <summary>
/// Converts boolean connection status to color for status indicator
/// </summary>
public class StatusColorConverter : IValueConverter
{
    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        if (value is bool isConnected)
        {
            return isConnected ? Colors.LimeGreen : Colors.OrangeRed;
        }
        return Colors.Gray;
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}

