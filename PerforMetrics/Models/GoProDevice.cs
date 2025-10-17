namespace PerforMetrics.Models;

/// <summary>
/// Represents a GoPro camera device
/// </summary>
public class GoProDevice
{
    /// <summary>
    /// Last 4 digits of GoPro serial number
    /// </summary>
    public string Identifier { get; set; } = string.Empty;

    /// <summary>
    /// Device name (e.g., "GoPro 8577")
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Bluetooth MAC address
    /// </summary>
    public string Address { get; set; } = string.Empty;

    /// <summary>
    /// Connection status
    /// </summary>
    public bool Connected { get; set; }

    /// <summary>
    /// IP address (for COHN devices)
    /// </summary>
    public string? IpAddress { get; set; }

    /// <summary>
    /// Whether certificate exists (for COHN devices)
    /// </summary>
    public bool CertificateExists { get; set; }
}

