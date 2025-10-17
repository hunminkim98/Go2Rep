# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 10:24:29 2025

@author: sshayeng-admin
"""

import re
import sys
import asyncio
import argparse
from typing import Any, List

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice as BleakDevice

from tutorial_modules import logger, noti_handler_T, GOPRO_BASE_UUID

# GoPro UUIDs for BLE Commands
class GoProUuid:
    COMMAND_REQ_UUID = GOPRO_BASE_UUID.format("0072")
    COMMAND_RSP_UUID = GOPRO_BASE_UUID.format("0073")


async def connect_to_gopros(notification_handler: noti_handler_T, max_cameras: int = 5) -> List[BleakClient]:
    """Connect to multiple GoPro cameras."""
    devices = {}
    matched_devices = []

    # Scan callback to discover GoPros
    def _scan_callback(device: BleakDevice, _: Any) -> None:
        if device.name and "GoPro" in device.name:
            devices[device.name] = device

    logger.info("Scanning for GoPro cameras...")
    
    # Scan for devices until at least one is found
    while len(matched_devices) == 0:
        await BleakScanner.discover(timeout=5, detection_callback=_scan_callback)
        matched_devices = list(devices.values())

    # Limit number of cameras to connect
    matched_devices = matched_devices[:max_cameras]
    logger.info(f"Found {len(matched_devices)} GoPro cameras.")

    clients = []
    for device in matched_devices:
        logger.info(f"Connecting to {device.name}...")
        client = BleakClient(device)
        await client.connect(timeout=15)

        # Enable notifications
        for service in client.services:
            for char in service.characteristics:
                if "notify" in char.properties:
                    await client.start_notify(char, notification_handler)

        clients.append(client)
        logger.info(f"Connected to {device.name}")

    return clients


async def send_command_to_gopros(clients: List[BleakClient], command: bytes) -> None:
    """Send a BLE command to multiple GoPro cameras."""
    request_uuid = GoProUuid.COMMAND_REQ_UUID
    tasks = [client.write_gatt_char(request_uuid, command, response=True) for client in clients]
    await asyncio.gather(*tasks)


async def main(max_cameras: int) -> None:
    async def dummy_notification_handler(*_: Any) -> None:
        pass

    clients = await connect_to_gopros(dummy_notification_handler, max_cameras)

    if not clients:
        logger.error("No GoPro cameras found.")
        return

    # Start recording
    logger.info("Starting capture on all cameras...")
    start_command = bytes([3, 1, 1, 1])
    await send_command_to_gopros(clients, start_command)

    await asyncio.sleep(2)  # Record for 2 seconds

    # Stop recording
    logger.info("Stopping capture on all cameras...")
    stop_command = bytes([3, 1, 1, 0])
    await send_command_to_gopros(clients, stop_command)

    # Disconnect from cameras
    await asyncio.gather(*(client.disconnect() for client in clients))
    logger.info("Disconnected from all cameras.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to multiple GoPro cameras and capture simultaneously.")
    parser.add_argument("-n", "--num_cameras", type=int, default=5, help="Maximum number of GoPros to connect to")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.num_cameras))
    except Exception as e:
        logger.error(e)
        sys.exit(-1)
    else:
        sys.exit(0)
