import asyncio
import time
import sys
from typing import Any, List

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

from tutorial_modules import GOPRO_BASE_UUID, logger

# GoPro BLE UUIDs
COMMAND_REQ_UUID = GOPRO_BASE_UUID.format("0072")

# Store timestamps
start_times = {}
stop_times = {}

async def discover_gopros() -> List[BLEDevice]:
    """Discover all available GoPro cameras via BLE."""
    devices = {}

    def _scan_callback(device: BLEDevice, _: Any) -> None:
        if device.name and "GoPro" in device.name:
            devices[device.name] = device

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

    try:
        await client.pair()
    except NotImplementedError:
        pass  # Expected behavior on macOS

    return client

async def start_recording(clients: List[BleakClient]) -> None:
    """Start recording on all connected GoPro cameras."""
    command = bytes([3, 1, 1, 1])  # Start recording command
    for client in clients:
        start_times[client.address] = time.time()  # Record timestamp
        logger.info(f"Starting recording on {client.address} at {start_times[client.address]:.6f} sec")
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)

async def stop_recording(clients: List[BleakClient]) -> None:
    """Stop recording on all connected GoPro cameras after a delay."""
    await asyncio.sleep(2)  # Wait for 2 seconds after user stops
    command = bytes([3, 1, 1, 0])  # Stop recording command
    for client in clients:
        stop_times[client.address] = time.time()  # Record timestamp
        logger.info(f"Stopping recording on {client.address} at {stop_times[client.address]:.6f} sec")
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)

    # Calculate time differences
    if start_times:
        first_start = min(start_times.values())
        last_start = max(start_times.values())
        start_diff = last_start - first_start
        logger.info(f"Start time difference: {start_diff:.6f} sec")

    if stop_times:
        first_stop = min(stop_times.values())
        last_stop = max(stop_times.values())
        stop_diff = last_stop - first_stop
        logger.info(f"Stop time difference: {stop_diff:.6f} sec")

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
