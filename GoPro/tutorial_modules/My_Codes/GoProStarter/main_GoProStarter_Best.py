import asyncio
import time
import sys
from typing import Any, List, Dict

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
import datetime
from tutorial_modules import GOPRO_BASE_UUID, logger

# GoPro BLE UUIDs
COMMAND_REQ_UUID = GOPRO_BASE_UUID.format("0072")

# Store timestamps and camera names
start_times: Dict[str, float] = {}
stop_times: Dict[str, float] = {}
camera_names: Dict[str, str] = {}  # Maps MAC address to GoPro name

async def discover_gopros() -> List[BLEDevice]:
    """Discover all available GoPro cameras via BLE."""
    devices = {}

    def _scan_callback(device: BLEDevice, _: Any) -> None:
        if device.name and "GoPro" in device.name:
            devices[device.address] = device

    logger.info("Scanning for GoPro cameras...")
    
    while not devices:
        await BleakScanner.discover(timeout=5, detection_callback=_scan_callback)

    logger.info(f"Discovered {len(devices)} GoPro camera(s).")
    return list(devices.values())

async def connect_camera(device: BLEDevice) -> BleakClient:
    """Establish BLE connection with a GoPro camera."""
    logger.info(f"Connecting to {device.name}...")
    client = BleakClient(device)
    await client.connect()
    logger.info(f"Connected to {device.name}")

    camera_names[device.address] = device.name  # Store the name of the camera

    try:
        await client.pair()
    except NotImplementedError:
        pass  # Expected behavior on macOS

    return client

async def start_recording(clients: List[BleakClient]) -> None:
    """Start recording on all connected GoPro cameras."""
    command = bytes([3, 1, 1, 1])  # Start recording command
    
    for client in clients:
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)
        start_times[client.address] = time.time()  # Record timestamp 
        human_readable_time = datetime.datetime.fromtimestamp(start_times[client.address]).strftime('%Y-%m-%d %H:%M:%S.%f')  
        logger.info(f"Starting recording on {camera_names[client.address]} at {human_readable_time}")        
async def stop_recording(clients: List[BleakClient]) -> None:
    """Stop recording on all connected GoPro cameras after a delay."""
    await asyncio.sleep(2)  # Wait for 2 seconds after user stops
    command = bytes([3, 1, 1, 0])  # Stop recording command
    for client in clients:
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)
        stop_times[client.address] = time.time()  # Record timestamp
        human_readable_time = datetime.datetime.fromtimestamp(stop_times[client.address]).strftime('%Y-%m-%d %H:%M:%S.%f')
        logger.info(f"Stopping recording on {camera_names[client.address]} at {human_readable_time}")
    # # Sort timestamps by start time
    # sorted_starts = sorted(start_times.items(), key=lambda x: x[1])
    # sorted_stops = sorted(stop_times.items(), key=lambda x: x[1])

    # if sorted_starts:
        # first_start = sorted_starts[0][1]
        # last_start = sorted_starts[-1][1]
        # start_diff = last_start - first_start
        # logger.info(f"Start time difference (First to Last): {start_diff:.6f} sec")

        # # Calculate time difference between consecutive cameras
        # for i in range(len(sorted_starts) - 1):
            # cam1, time1 = sorted_starts[i]
            # cam2, time2 = sorted_starts[i + 1]
            # logger.info(f"Start time difference ({camera_names[cam1]} → {camera_names[cam2]}): {time2 - time1:.6f} sec")

    # if sorted_stops:
        # first_stop = sorted_stops[0][1]
        # last_stop = sorted_stops[-1][1]
        # stop_diff = last_stop - first_stop
        # logger.info(f"Stop time difference (First to Last): {stop_diff:.6f} sec")

        # # Calculate time difference between consecutive cameras
        # for i in range(len(sorted_stops) - 1):
            # cam1, time1 = sorted_stops[i]
            # cam2, time2 = sorted_stops[i + 1]
            # logger.info(f"Stop time difference ({camera_names[cam1]} → {camera_names[cam2]}): {time2 - time1:.6f} sec")

async def main():
    # Discover and connect to all available GoPro cameras
    devices = await discover_gopros()
    clients = await asyncio.gather(*[connect_camera(device) for device in devices])

    # Start recording
    await start_recording(clients)

    # Wait for user input to stop
    input("Press Enter to stop recording...")

    # Stop recording after 2 seconds
    await stop_recording(clients)

    # Disconnect all cameras
    for client in clients:
        await client.disconnect()
    logger.info("Disconnected from all cameras.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(0)
