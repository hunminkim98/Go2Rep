import asyncio
import re
import sys
import argparse
from typing import Any, List

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

from tutorial_modules import GOPRO_BASE_UUID, logger

# GoPro BLE UUID for starting/stopping capture
COMMAND_REQ_UUID = GOPRO_BASE_UUID.format("0072")
COMMAND_RSP_UUID = GOPRO_BASE_UUID.format("0073")

# Function to discover all GoPro cameras
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

# Function to connect to a GoPro camera
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

# Function to start recording on all cameras
async def start_recording(clients: List[BleakClient]) -> None:
    """Start recording on all connected GoPro cameras."""
    command = bytes([3, 1, 1, 1])  # Start recording command
    for client in clients:
        logger.info(f"Starting recording on {client.address}...")
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)
    logger.info("All cameras started recording.")

# Function to stop recording on all cameras
async def stop_recording(clients: List[BleakClient]) -> None:
    """Stop recording on all connected GoPro cameras after a delay."""
    await asyncio.sleep(2)  # Wait for 2 seconds after user stops
    command = bytes([3, 1, 1, 0])  # Stop recording command
    for client in clients:
        logger.info(f"Stopping recording on {client.address}...")
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)
    logger.info("All cameras stopped recording.")

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
