# gopro_settings.py

import asyncio
import logging
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import nest_asyncio
from typing import Callable
from bleak.backends.device import BLEDevice
import threading
import logging
from tutorial_modules import logger, GoProUuid

logger = logging.getLogger(__name__)

# Function to scan for Bluetooth devices and filter out GoPros
async def scan_bluetooth_devices():
    matched_devices = []
    devices = await BleakScanner.discover()
    if not devices:
        print("No Bluetooth devices found.")
    else:
        print(f"Found {len(devices)} devices:")
        for device in devices:
            if device.name and "GoPro" in device.name:
                matched_devices.append(device)
                
    return matched_devices

async def connect_ble(notification_handler: Callable, device: BLEDevice) -> BleakClient:
    logger.info(f"Connecting to {device.name} ({device.address})...")

    client = BleakClient(device, disconnected_callback=lambda _: logger.warning(f"Disconnected from {device.name}"))

    await client.connect()
    logger.info(f"Connected to {device.name}")

    # No need for get_services() anymore — services are already loaded

    for service in client.services:
        for char in service.characteristics:
            if "notify" in char.properties:
                await client.start_notify(char.uuid, notification_handler)

    return client
    
async def apply_settings_to_gopro_devices(fps, resolution, gopro_list, root=None):
    matched_devices = []
    
    # Check if all the GoPros are discoverable
    if not gopro_list:       
        matched_devices = await scan_bluetooth_devices()   
    else:
        attempts = 0
        max_attempts = 2
        while attempts < max_attempts:
            logger.info(f"Discovery attempt {attempts + 1}...")
            devices = await scan_bluetooth_devices()
            found_names = [device.name for device in devices]
    
            matched_devices = [device for device in devices if device.name in gopro_list]
            missing_names = [name for name in gopro_list if name not in found_names]
    
            if not missing_names:
                logger.info("All GoPro cameras found.")
                break
    
            attempts += 1
            logger.warning(f"Missing devices after attempt {attempts}: {missing_names}")
            await asyncio.sleep(1)
    
        if missing_names:
            while True:
                response = messagebox.askyesnocancel(
                    "Cameras Not Found",
                    f"The following GoPros could not be found:\n{', '.join(missing_names)}\n\n"
                    "Do you want to continue anyway?\n\n"
                    "Yes = Continue with available cameras\n"
                    "No = Search again\n"
                    "Cancel = Cancel"
                )
                if response is True:
                    logger.warning("Continuing with partial camera list.")
                    break
                elif response is False:
                    logger.info("Retrying discovery...")
                    return await apply_settings_to_gopro_devices(fps, resolution, gopro_list, root)
                elif response is None:
                    logger.error("ERROR: User aborted due to missing GoPros.")
                    raise RuntimeError("User aborted due to missing GoPros.")
    
    print(f"Devices are: {matched_devices}")
    
    if matched_devices:
        # Map FPS to corresponding command bytes
        if fps == 60:
            logger.info("Setting the fps to 60")
            fps_request = bytes([0x03, 0x03, 0x01, 0x02])
        elif fps == 120:
            logger.info("Setting the fps to 120")
            fps_request = bytes([0x03, 0x03, 0x01, 0x01])
        elif fps == 240:
            logger.info("Setting the fps to 240")
            fps_request = bytes([0x03, 0x03, 0x01, 0x00])
    
        # Map resolution to corresponding command bytes
        if resolution == 1080:
            logger.info("Setting the resolution to 1080p")
            resolution_request = bytes([0x03, 0x02, 0x01, 0x09])  # 1080p
        elif resolution == 2700:  # 2.7K resolution
            logger.info("Setting the resolution to 2.7K")
            resolution_request = bytes([0x03, 0x02, 0x01, 0x04])  # 2.7K
        elif resolution == 4000:  # 4K resolution
            logger.info("Setting the resolution to 4K")
            resolution_request = bytes([0x03, 0x02, 0x01, 0x01])  # 4K
        else:
            logger.error("Unknown resolution")
            return
        clients = []
        # Iterate over matched GoPro devices
        for device in matched_devices:
            try:
                identifier = device.name.split(" ")[-1]  # Extract GoPro identifier (last 4 digits)
                logger.info(f"Processing GoPro: {identifier}")

                # Connect to GoPro via BLE (only once per device)
                event = asyncio.Event()

                async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
                    uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
                    logger.info(f'Received response at {uuid}: {data.hex(":")}')
                    if uuid == GoProUuid.SETTINGS_RSP_UUID and data[2] == 0x00:
                        logger.info("Command sent successfully")
                    else:
                        logger.error("Unexpected response")
                    event.set()

                client: BleakClient = await connect_ble(notification_handler, device)
                clients.append((client, event))

            except Exception as e:
                logger.error(f"Error connecting to GoPro {identifier}: {e}")

        # Write the FPS and resolution settings to all connected GoPro cameras
        for client, event in clients:
            try:
                # Write the FPS setting to the GoPro camera
                logger.debug(f"Writing to {GoProUuid.SETTINGS_REQ_UUID}: {fps_request.hex(':')}")
                event.clear()
                await client.write_gatt_char(GoProUuid.SETTINGS_REQ_UUID.value, fps_request, response=True)
                await event.wait()  # Wait to receive the notification response

                # Write the resolution setting to the GoPro camera
                logger.debug(f"Writing to {GoProUuid.SETTINGS_REQ_UUID}: {resolution_request.hex(':')}")
                event.clear()
                await client.write_gatt_char(GoProUuid.SETTINGS_REQ_UUID.value, resolution_request, response=True)
                await event.wait()  # Wait to receive the notification response

            except Exception as e:
                logger.error(f"Error applying settings: {e}")

        # Disconnect from the GoPro
        for client, _ in clients:
            try:
                await client.disconnect()
                logger.info("Disconnected from GoPro")
            except Exception as e:
                logger.error(f"Error disconnecting GoPro: {e}")
        if matched_devices:
            root.after(0, lambda: messagebox.showinfo("Success", "Settings applied to all detected GoPro devices."))
            
        else:
            root.after(0, lambda: messagebox.showwarning("No Devices", "No GoPro devices detected."))
