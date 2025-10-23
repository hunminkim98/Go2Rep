using System;
using System.Globalization;
using Avalonia.Data.Converters;

namespace PerforMetrics.Converters;

/// <summary>
/// Converts boolean values to custom strings based on parameter
/// Parameter format: "TrueString|FalseString"
/// </summary>
public class BoolToStringConverter : IValueConverter
{
    public static readonly BoolToStringConverter Instance = new();

    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        if (value is bool boolValue && parameter is string paramString)
        {
            var parts = paramString.Split('|');
            if (parts.Length == 2)
            {
                return boolValue ? parts[0] : parts[1];
            }
        }
        
        // Default fallback
        return value?.ToString() ?? string.Empty;
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }
}

