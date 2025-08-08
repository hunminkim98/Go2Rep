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
    matched_devices = await scan_bluetooth_devices()
    if not matched_devices:
        print("No GoPro cameras found.")
        return

    for device in matched_devices:
        try:
            identifier = device.name.split(" ")[-1]
            logger.info(f"Connecting to GoPro: {identifier}")
            event = asyncio.Event()

            async def notification_handler(characteristic, data):
                uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
                logger.info(f'Received: {uuid} - {data.hex(":")}')
                event.set()

            client: BleakClient = await connect_ble(notification_handler, identifier)
            logger.info(f"Connected to GoPro {identifier}")
            await client.disconnect()
            logger.info(f"Disconnected from GoPro {identifier}")

        except Exception as e:
            logger.error(f"Error connecting to GoPro {identifier}: {e}")

    return [device.name for device in matched_devices]
