import asyncio
from bleak import BleakClient, BleakScanner
from tutorial_modules import connect_ble, logger, GoProUuid

async def scan_bluetooth_devices():
    matched_devices = []
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name and "GoPro" in device.name:
            matched_devices.append(device)
    return matched_devices

async def main(identifier=None, timeout=None):
    # Detect all available GoPros
    matched_devices = await scan_bluetooth_devices()

    if not matched_devices:
        print("No GoPro cameras found.")
        return

    print(f"Found {len(matched_devices)} GoPro cameras:")  
    
    for device in matched_devices:
        # Assuming 'device' has an attribute 'name' that contains the name of the device
        print(f"Device name: {device.name}")
        
    return [device.name for device in matched_devices]
    
    
