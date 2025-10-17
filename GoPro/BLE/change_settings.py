import sys
import asyncio
import argparse
import os
import platform
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from tutorial_modules import connect_ble, logger, GoProUuid


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


# Main function to connect to GoPro devices and change FPS and resolution
async def main(identifier: str | None, timeout: int | None) -> None:
    # Detect all available GoPros
    matched_devices = await scan_bluetooth_devices()

    # Ask user for FPS
    while True:
        try:
            fps = int(input("Enter the desired FPS (60, 120, 240): "))
            if fps in [60, 120, 240]:
                break
            else:
                print("Invalid FPS value. Please enter one of 60, 120, or 240.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Ask user for resolution
    while True:
        try:
            resolution = int(input("Enter the desired resolution (1080, 2700 for 2.7K, 4000 for 4K): "))
            if resolution in [1080, 2700, 4000]:
                break
            else:
                print("Invalid resolution value. Please enter one of 1080, 2700, or 4000.")
        except ValueError:
            print("Invalid input. Please enter a number.")

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

    # Iterate over matched GoPro devices
    for device in matched_devices:
        try:
            identifier = device.name.split(" ")[-1]  # Extract GoPro identifier (last 4 digits)
            logger.info(f"Processing GoPro: {identifier}")

            # Connect to GoPro via BLE
            event = asyncio.Event()

            async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
                uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
                logger.info(f'Received response at {uuid}: {data.hex(":")}')

                if uuid == GoProUuid.SETTINGS_RSP_UUID and data[2] == 0x00:
                    logger.info("Command sent successfully")
                else:
                    logger.error("Unexpected response")

                event.set()

            client: BleakClient = await connect_ble(notification_handler, identifier)

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

            # Disconnect from the GoPro
            await client.disconnect()
            logger.info(f"Disconnected from GoPro {identifier}")

        except Exception as e:
            logger.error(f"Error processing GoPro {identifier}: {e}")


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Allow nested event loops

    parser = argparse.ArgumentParser(description="Connect to GoPro cameras and change their FPS and resolution.")
    parser.add_argument("-i", "--identifier", type=str, help="Last 4 digits of GoPro serial number", default=None)
    parser.add_argument("-t", "--timeout", type=int, help="Time in seconds to maintain connection before disconnecting", default=None)
    args = parser.parse_args()

    try:
        asyncio.run(main(args.identifier, args.timeout))
    except Exception as e:
        logger.error(e)
        sys.exit(-1)
    else:
        sys.exit(0)
