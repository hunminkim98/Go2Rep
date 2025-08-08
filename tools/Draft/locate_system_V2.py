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
    
    # Iterate over matched GoPro devices
    for device in matched_devices:
        try:
            identifier = device.name.split(" ")[-1]  # Extract GoPro identifier (last 4 digits)
            logger.info(f"Connecting to GoPro: {identifier}")

            # Connect to GoPro via BLE
            event = asyncio.Event()

            async def notification_handler(characteristic, data: bytearray) -> None:
                uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
                logger.info(f'Received response at {uuid}: {data.hex(":")}')
                event.set()

            # Connect to the GoPro device
            client: BleakClient = await connect_ble(notification_handler, identifier)

            # Wait for the connection to be established
            logger.info(f"Connected to GoPro {identifier}")

            # You can perform additional operations here if needed

            # Disconnect from the GoPro
            await client.disconnect()
            logger.info(f"Disconnected from GoPro {identifier}")

        except Exception as e:
            logger.error(f"Error connecting to GoPro {identifier}: {e}")
    
    print(f"Summary: The following devices are available for recording:")
    for device in matched_devices:
        # Assuming 'device' has an attribute 'name' that contains the name of the device
        print(f"Device name: {device.name}")
        
    return [device.name for device in matched_devices]
    
    
