import sys
import asyncio
import argparse
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from tutorial_modules import GoProUuid, logger, connect_ble

async def connect_and_enable_wifi(identifier: str | None = None) -> tuple[str, str, BleakClient]:
    """Connect to a GoPro via BLE, pair, enable notifications, find its WiFi AP SSID and password, and enable its WiFi AP"""
    event = asyncio.Event()
    client: BleakClient

    async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
        logger.info(f'Received response at {uuid}: {data.hex(":")}')
        if uuid is GoProUuid.COMMAND_RSP_UUID and data[2] == 0x00:
            logger.info("Command sent successfully")
        else:
            logger.error("Unexpected response")
        event.set()

    client = await connect_ble(notification_handler, identifier)

    # Read WiFi SSID
    ssid_uuid = GoProUuid.WIFI_AP_SSID_UUID
    logger.info(f"Reading WiFi AP SSID at {ssid_uuid}")
    ssid = (await client.read_gatt_char(ssid_uuid.value)).decode()
    logger.info(f"SSID: {ssid}")

    # Read WiFi Password
    password_uuid = GoProUuid.WIFI_AP_PASSWORD_UUID
    logger.info(f"Reading WiFi AP password at {password_uuid}")
    password = (await client.read_gatt_char(password_uuid.value)).decode()
    logger.info(f"Password: {password}")

    # Enable WiFi AP
    logger.info("Enabling WiFi AP")
    event.clear()
    request = bytes([0x03, 0x17, 0x01, 0x01])
    command_request_uuid = GoProUuid.COMMAND_REQ_UUID
    await client.write_gatt_char(command_request_uuid.value, request, response=True)
    await event.wait()
    logger.info("WiFi AP enabled")

    return ssid, password, client

async def main(identifier: str | None, timeout: int | None) -> None:
    *_, client = await connect_and_enable_wifi(identifier)
    if timeout:
        logger.info(f"Maintaining BLE connection for {timeout} seconds")
        await asyncio.sleep(timeout)
    else:
        input("Maintaining BLE Connection indefinitely. Press enter to exit.")
    logger.info("Disconnecting BLE...")
    await client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to a GoPro via BLE, enable WiFi AP, and retrieve credentials.")
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
