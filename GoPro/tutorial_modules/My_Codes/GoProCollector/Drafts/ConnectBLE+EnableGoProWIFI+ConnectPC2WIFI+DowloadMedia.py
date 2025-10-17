# -*- coding: utf-8 -*-
"""
Combined Script: Connect to GoPro via BLE, Enable WiFi, Connect to WiFi, and Download Media
"""

import sys
import asyncio
import argparse
import os
import requests
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bs4 import BeautifulSoup
from tutorial_modules import GoProUuid, logger, connect_ble

GOPRO_BASE_URL = "http://10.5.5.9/videos/DCIM/100GOPRO/"
GOPRO_BASE_URL_2Download="http://10.5.5.9"

async def connect_and_enable_wifi(identifier: str | None = None) -> tuple[str, str, BleakClient]:
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

    ssid = (await client.read_gatt_char(GoProUuid.WIFI_AP_SSID_UUID.value)).decode()
    password = (await client.read_gatt_char(GoProUuid.WIFI_AP_PASSWORD_UUID.value)).decode()

    logger.info("Enabling WiFi AP")
    event.clear()
    request = bytes([0x03, 0x17, 0x01, 0x01])
    await client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, request, response=True)
    await event.wait()
    logger.info("WiFi AP enabled")

    return ssid, password, client

def connect_to_wifi(ssid: str, password: str):
    logger.info(f"Connecting to WiFi: {ssid}")
    if os.name == "nt":
        os.system(f'netsh wlan connect name="{ssid}" ssid="{ssid}" interface="Wi-Fi"')
    else:
        os.system(f'nmcli device wifi connect "{ssid}" password "{password}"')

def get_media_list():
    logger.info(f"Fetching media list from {GOPRO_BASE_URL}")
    response = requests.get(GOPRO_BASE_URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    return [link['href'] for link in soup.find_all('a', href=True) if link['href'].lower().endswith('.mp4')]

def download_file(file_name):
    # Correctly construct the file URL by concatenating the base URL and the filename.
    file_url = f"{GOPRO_BASE_URL_2Download}{file_name}"
    logger.info(f"Downloading {file_name} from {file_url}")
    
    # Extract the directory part of the file path
    directory = os.path.dirname(file_name)
    
    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Proceed to download the file
    with requests.get(file_url, stream=True, timeout=10) as request:
        request.raise_for_status()  # Will raise HTTPError for bad responses
        with open(file_name, "wb") as f:
            for chunk in request.iter_content(chunk_size=8192):
                f.write(chunk)
    logger.info(f"Downloaded file saved to {directory}")


def download_media():
    media_files = get_media_list()
    for file in media_files:
        download_file(file)

async def main(identifier: str | None, timeout: int | None) -> None:
    ssid, password, client = await connect_and_enable_wifi(identifier)
    connect_to_wifi(ssid, password)
    await asyncio.sleep(5)  # Allow time for WiFi connection
    download_media()
    logger.info("Disconnecting BLE...")
    await client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to a GoPro via BLE, enable WiFi AP, connect to WiFi, and download media.")
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
