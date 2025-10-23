using System;
using CommunityToolkit.Mvvm.ComponentModel;

namespace PerforMetrics.Models;

/// <summary>
/// Represents a GoPro camera device
/// </summary>
public partial class GoProDevice : ObservableObject
{
    /// <summary>
    /// Last 4 digits of GoPro serial number
    /// </summary>
    [ObservableProperty]
    private string _identifier = string.Empty;

    /// <summary>
    /// Device name (e.g., "GoPro 8577")
    /// </summary>
    [ObservableProperty]
    private string _name = string.Empty;

    /// <summary>
    /// Bluetooth MAC address
    /// </summary>
    [ObservableProperty]
    private string _address = string.Empty;

    /// <summary>
    /// Connection status
    /// </summary>
    [ObservableProperty]
    private bool _connected;

    /// <summary>
    /// IP address (for COHN devices)
    /// </summary>
    [ObservableProperty]
    private string? _ipAddress;

    /// <summary>
    /// Whether certificate exists (for COHN devices)
    /// </summary>
    [ObservableProperty]
    private bool _certificateExists;

    /// <summary>
    /// Last time connection health was checked
    /// </summary>
    [ObservableProperty]
    private DateTime? _lastHealthCheck;

    /// <summary>
    /// Current reconnection status
    /// </summary>
    [ObservableProperty]
    private string _reconnectionStatus = string.Empty;

    /// <summary>
    /// Whether this device is currently attempting to reconnect
    /// </summary>
    [ObservableProperty]
    private bool _isReconnecting;
}

