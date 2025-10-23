using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PerforMetrics.Models;
using PerforMetrics.Services;

namespace PerforMetrics.ViewModels;

/// <summary>
/// ViewModel for reconnection dialog
/// Manages automatic reconnection attempts for disconnected GoPro devices
/// </summary>
public partial class ReconnectionDialogViewModel : ViewModelBase
{
    private readonly ApiService _apiService;
    private CancellationTokenSource? _cancellationTokenSource;

    [ObservableProperty]
    private ObservableCollection<GoProDevice> _disconnectedDevices;

    [ObservableProperty]
    private bool _isReconnecting;

    [ObservableProperty]
    private string _overallStatus = "재연결을 시도하고 있습니다...";

    [ObservableProperty]
    private int _totalDevices;

    [ObservableProperty]
    private int _reconnectedDevices;

    [ObservableProperty]
    private int _failedDevices;

    /// <summary>
    /// Event raised when dialog should be closed
    /// </summary>
    public event EventHandler<bool>? RequestClose;

    public ReconnectionDialogViewModel(ObservableCollection<GoProDevice> disconnectedDevices)
    {
        _apiService = new ApiService();
        _disconnectedDevices = new ObservableCollection<GoProDevice>(disconnectedDevices);
        _totalDevices = disconnectedDevices.Count;
        
        // Start reconnection attempts automatically
        _ = StartReconnectionAsync();
    }

    /// <summary>
    /// Start automatic reconnection process
    /// </summary>
    private async Task StartReconnectionAsync()
    {
        IsReconnecting = true;
        _cancellationTokenSource = new CancellationTokenSource();
        
        try
        {
            // Attempt to reconnect each device
            foreach (var device in DisconnectedDevices)
            {
                if (_cancellationTokenSource.Token.IsCancellationRequested)
                {
                    OverallStatus = "재연결이 취소되었습니다.";
                    break;
                }

                await ReconnectDeviceAsync(device, _cancellationTokenSource.Token);
            }

            // Update overall status
            if (!_cancellationTokenSource.Token.IsCancellationRequested)
            {
                if (FailedDevices == 0)
                {
                    OverallStatus = $"모든 장치가 성공적으로 재연결되었습니다. ({ReconnectedDevices}/{TotalDevices})";
                }
                else if (ReconnectedDevices == 0)
                {
                    OverallStatus = $"모든 재연결 시도가 실패했습니다. ({FailedDevices}/{TotalDevices})";
                }
                else
                {
                    OverallStatus = $"일부 장치 재연결 완료. 성공: {ReconnectedDevices}, 실패: {FailedDevices}";
                }

                // Auto-close after 2 seconds if all succeeded
                if (FailedDevices == 0)
                {
                    await Task.Delay(2000);
                    RequestClose?.Invoke(this, true);
                }
            }
        }
        finally
        {
            IsReconnecting = false;
        }
    }

    /// <summary>
    /// Attempt to reconnect a single device with retries
    /// </summary>
    private async Task ReconnectDeviceAsync(GoProDevice device, CancellationToken cancellationToken)
    {
        const int MaxRetries = 3;
        const int RetryDelayMs = 2000;

        device.IsReconnecting = true;
        device.ReconnectionStatus = "재연결 시도 중...";

        for (int attempt = 1; attempt <= MaxRetries; attempt++)
        {
            if (cancellationToken.IsCancellationRequested)
            {
                device.ReconnectionStatus = "취소됨";
                device.IsReconnecting = false;
                return;
            }

            try
            {
                // Update status
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    device.ReconnectionStatus = $"시도 {attempt}/{MaxRetries}...";
                });

                // Attempt reconnection
                bool success = await _apiService.ReconnectGoProAsync(device.Identifier);

                if (success)
                {
                    // Verify connection
                    await Task.Delay(500, cancellationToken);
                    bool isHealthy = await _apiService.CheckDeviceConnectionAsync(device.Identifier);

                    if (isHealthy)
                    {
                        await Dispatcher.UIThread.InvokeAsync(() =>
                        {
                            device.Connected = true;
                            device.ReconnectionStatus = "재연결 성공";
                            device.IsReconnecting = false;
                            ReconnectedDevices++;
                        });
                        return;
                    }
                }

                // If not last attempt, wait before retry
                if (attempt < MaxRetries)
                {
                    await Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        device.ReconnectionStatus = $"재시도 대기 중... ({RetryDelayMs / 1000}초)";
                    });
                    await Task.Delay(RetryDelayMs, cancellationToken);
                }
            }
            catch (Exception ex)
            {
                if (attempt == MaxRetries)
                {
                    await Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        device.ReconnectionStatus = $"실패: {ex.Message}";
                        device.IsReconnecting = false;
                        FailedDevices++;
                    });
                }
            }
        }

        // All retries failed
        await Dispatcher.UIThread.InvokeAsync(() =>
        {
            device.ReconnectionStatus = "재연결 실패";
            device.IsReconnecting = false;
            FailedDevices++;
        });
    }

    /// <summary>
    /// Cancel all reconnection attempts
    /// </summary>
    [RelayCommand]
    private void CancelReconnection()
    {
        _cancellationTokenSource?.Cancel();
        OverallStatus = "재연결을 취소하는 중...";
        
        // Close dialog after short delay
        Task.Delay(500).ContinueWith(_ =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                RequestClose?.Invoke(this, false);
            });
        });
    }

    /// <summary>
    /// Retry reconnection for a specific device
    /// </summary>
    [RelayCommand]
    private async Task RetryDeviceAsync(string identifier)
    {
        var device = DisconnectedDevices.FirstOrDefault(d => d.Identifier == identifier);
        if (device == null || device.IsReconnecting) return;

        // Create new cancellation token for this single retry
        using var cts = new CancellationTokenSource();
        await ReconnectDeviceAsync(device, cts.Token);
    }

    /// <summary>
    /// Skip reconnection for a specific device
    /// </summary>
    [RelayCommand]
    private void SkipDevice(string identifier)
    {
        var device = DisconnectedDevices.FirstOrDefault(d => d.Identifier == identifier);
        if (device == null) return;

        device.ReconnectionStatus = "건너뜀";
        device.IsReconnecting = false;
        FailedDevices++;
    }

    /// <summary>
    /// Close the dialog
    /// </summary>
    [RelayCommand]
    private void CloseDialog()
    {
        _cancellationTokenSource?.Cancel();
        RequestClose?.Invoke(this, ReconnectedDevices > 0);
    }

    /// <summary>
    /// Cleanup resources
    /// </summary>
    public void Dispose()
    {
        _cancellationTokenSource?.Cancel();
        _cancellationTokenSource?.Dispose();
    }
}


