import asyncio
import time
import datetime
from typing import List, Dict, Any
from tkinter import messagebox

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

from tutorial_modules import GOPRO_BASE_UUID, logger

COMMAND_REQ_UUID = GOPRO_BASE_UUID.format("0072")

start_times: Dict[str, float] = {}
stop_times: Dict[str, float] = {}
camera_names: Dict[str, str] = {}

async def discover_gopros() -> List[BLEDevice]:
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
    logger.info(f"Connecting to {device.name}...")
    client = BleakClient(device)
    await client.connect()
    logger.info(f"Connected to {device.name}")

    camera_names[device.address] = device.name

    try:
        await client.pair()
    except NotImplementedError:
        pass

    return client

async def start_recording(clients: List[BleakClient]) -> None:
    command = bytes([3, 1, 1, 1])

    for client in clients:
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)
        start_times[client.address] = time.time()
        human_readable = datetime.datetime.fromtimestamp(start_times[client.address]).strftime('%Y-%m-%d %H:%M:%S.%f')
        logger.info(f"Started recording on {camera_names[client.address]} at {human_readable}")

async def stop_recording(clients: List[BleakClient]) -> None:
    await asyncio.sleep(2)
    command = bytes([3, 1, 1, 0])

    for client in clients:
        await client.write_gatt_char(COMMAND_REQ_UUID, command, response=True)
        stop_times[client.address] = time.time()
        human_readable = datetime.datetime.fromtimestamp(stop_times[client.address]).strftime('%Y-%m-%d %H:%M:%S.%f')
        logger.info(f"Stopped recording on {camera_names[client.address]} at {human_readable}")

async def discover_and_initialize_gopros(gopro_list: List[str]):
    
    matched_devices = []
    
    # Check if all the GoPros are discoverable
    if not gopro_list:       
        matched_devices = await discover_gopros()   
    else:
        attempts = 0
        max_attempts = 2
    
        while attempts < max_attempts:
            logger.info(f"Discovery attempt {attempts + 1}...")
            devices = await discover_gopros()
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
                    "No = Search again \n"
                    "Cancel = Cancel"
                )
                
                if response is True:
                    logger.warning("Continuing with partial camera list.")
                    break
                elif response is False:
                    logger.info("User selected retry. Restarting search attempts...")
                    return await discover_and_initialize_gopros(gopro_list)
                elif response is None:
                    raise RuntimeError("User aborted due to missing GoPros.")

    print(f"Devices are: {matched_devices}")
    clients = await asyncio.gather(*[connect_camera(device) for device in matched_devices])
    return clients

async def start_all(clients):
    await start_recording(clients)

async def stop_all(clients):
    await stop_recording(clients)

async def disconnect_all(clients):
    for client in clients:
        await client.disconnect()
    logger.info("Disconnected from all GoPro cameras.")
