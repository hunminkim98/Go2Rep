# -*- coding: utf-8 -*-
"""
Enhanced Script: Connect to GoPro via BLE, Enable WiFi, Connect to WiFi, and Download Selected Media by Date
"""
import sys
import asyncio
import re
import argparse
import os
import time
import requests
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice as BleakDevice
from bs4 import BeautifulSoup
from tutorial_modules import GoProUuid, logger, connect_ble
from datetime import datetime
from typing import Any
import platform
import subprocess

GOPRO_BASE_URL = "http://10.5.5.9/videos/DCIM/100GOPRO/"
GOPRO_BASE_URL_2Download = "http://10.5.5.9"

async def connect_and_enable_wifi(identifier: str | None = None) -> tuple[str, str, BleakClient]:
    event = asyncio.Event()
    client: BleakClient

    async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
        logger.info(f'Received response at {uuid}: {data.hex(":")}')
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

def is_connected_to_wifi() -> bool:
    response = os.system("ping -n 1 10.5.5.9")  # Windows
    # response = os.system("ping -c 1 10.5.5.9")  # Linux
    return response == 0

def get_available_networks():
    """Scan and return a list of available WiFi SSIDs."""
    networks = []
    if os.name == "nt":
        output = subprocess.run(["netsh", "wlan", "show", "network"], capture_output=True, text=True).stdout
        networks = [line.split(":")[1].strip() for line in output.split("\n") if "SSID" in line]
    else:
        output = subprocess.run(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], capture_output=True, text=True).stdout
        networks = output.split("\n")
    return [ssid for ssid in networks if ssid]

def connect_to_wifi(ssid: str, password: str, retries: int = 5, delay: int = 20):
    logger.info(f"Connecting to WiFi: {ssid}, password: {password}")
    attempt = 0
    while attempt < retries:
        attempt += 1
        available_networks = get_available_networks()

        if ssid not in available_networks:
            logger.warning(f"Wi-Fi '{ssid}' not found in available networks. Retrying in {delay} seconds...")
            time.sleep(delay)
            continue  # Instead of returning, continue looping

        logger.info(f"Attempt {attempt}/{retries}")
        if os.name == "nt":
            os.system(f'netsh wlan connect name="{ssid}" ssid="{ssid}" interface="Wi-Fi"')
        else:
            os.system(f'nmcli device wifi connect "{ssid}" password "{password}"')

        time.sleep(delay)

        if is_connected_to_wifi():
            logger.info("Successfully connected to Wi-Fi!")
            return
        
        logger.warning(f"Wi-Fi connection failed on attempt {attempt}. Retrying...")

    logger.error(f"Failed to connect to Wi-Fi after {retries} attempts.")

def get_media_list():
    logger.info(f"Fetching media list from {GOPRO_BASE_URL}")
    response = requests.get(GOPRO_BASE_URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract file links and corresponding dates
    media_data = []
    for row in soup.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) >= 2:
            link = columns[0].find('a', href=True)
            date_text = columns[1].get_text(strip=True)

            if link and date_text and date_text != "-":  # Vérification supplémentaire
                try:
                    date_only = datetime.strptime(date_text, "%d-%b-%Y %H:%M").strftime("%d-%b-%Y")
                    media_data.append((link['href'], date_only))
                except ValueError:
                    logger.warning(f"Skipping file due to unexpected date format: {date_text}")

    return media_data

def prompt_user_for_date_and_time(media_data):
    # Extract unique dates and times
    unique_dates = sorted(set(date for _, date in media_data))

    if not unique_dates:
        logger.info("No media files found.")
        sys.exit(0)

    # Display available dates without repetition
    print("\nAvailable video dates:")
    for idx, date in enumerate(unique_dates, start=1):
        print(f"{idx}. {date}")

    # Ask user for a date selection
    while True:
        try:
            choice = int(input("\nEnter the number corresponding to the date you want to download: "))
            if 1 <= choice <= len(unique_dates):
                selected_date = unique_dates[choice - 1]  # Return only the selected date (not time)
                break
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    # Ask if the user wants all videos or specific hour range
    all_or_specific = input(f"Do you want to download all videos for {selected_date}? (y/n): ").strip().lower()

    if all_or_specific == 'y':
        # If 'yes', return all files for the selected date
        return selected_date, None, None
    else:
        # If 'no', ask for specific hours
        print("Please enter the time range (24-hour format, e.g., 14:00 - 16:00):")
        start_hour = input("Start hour (HH:MM): ").strip()
        end_hour = input("End hour (HH:MM): ").strip()

        # Return the date with the specific hour range
        return selected_date, start_hour, end_hour

def download_file(file_name):
    file_url = f"{GOPRO_BASE_URL_2Download}{file_name}"
    logger.info(f"Downloading {file_name} from {file_url}")
    
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    with requests.get(file_url, stream=True, timeout=10) as request:
        request.raise_for_status()
        with open(file_name, "wb") as f:
            for chunk in request.iter_content(chunk_size=8192):
                f.write(chunk)
    
    logger.info(f"Downloaded file saved to {directory}")

def download_selected_media_ask_user():
    media_files = get_media_list()
    
    if not media_files:
        logger.info("No media files found on the GoPro.")
        return

    selected_date, start_hour, end_hour = prompt_user_for_date_and_time(media_files)

    # Filter videos based on selected date and time range
    if start_hour and end_hour:
        files_to_download = [
            file for file, date in media_files if date == selected_date
            and start_hour <= file.split("-")[1][:5] <= end_hour
        ]
    else:
        files_to_download = [file for file, date in media_files if date == selected_date]

    if not files_to_download:
        logger.info(f"No videos found for {selected_date}.")
        return

    logger.info(f"Downloading videos for {selected_date}...")
    for file in files_to_download:
        download_file(file)
        
    return(selected_date, start_hour, end_hour)

def download_selected_media(selected_date, start_hour, end_hour):
    media_files = get_media_list()
    
    if not media_files:
        logger.info("No media files found on the GoPro.")
        return

    # selected_date, start_hour, end_hour = prompt_user_for_date_and_time(media_files)

    # Filter videos based on selected date and time range
    if start_hour and end_hour:
        files_to_download = [
            file for file, date in media_files if date == selected_date
            and start_hour <= file.split("-")[1][:5] <= end_hour
        ]
    else:
        files_to_download = [file for file, date in media_files if date == selected_date]

    if not files_to_download:
        logger.info(f"No videos found for {selected_date}.")
        return

    logger.info(f"Downloading videos for {selected_date}...")
    for file in files_to_download:
        download_file(file)
        
    
    
async def scan_bluetooth_devices():
    print("Scanning for Bluetooth devices...")
    matched_devices = []
    devices = await BleakScanner.discover()
    if not devices:
        print("No Bluetooth devices found.")
    else:
        A = 1
        print(f"Found {len(devices)} devices:")
        for device in devices:
            # Check if the device name contains "GoPro"
            if device.name and "GoPro" in device.name:
                matched_devices.append(device)
                
    return matched_devices
    
async def main(identifier: str | None, timeout: int | None) -> None:
    selected_date=[];
    start_hour=[]; 
    end_hour=[];
    # Detect all available GoPros
    matched_devices = await scan_bluetooth_devices()
    print(f"Devices are: {matched_devices}")
    # Print matched GoPro devices
    for device in matched_devices:
        # Disconnect the PC from the current WiFi
        if platform.system() == "Windows":
            os.system("netsh wlan disconnect")
        else:
            os.system("nmcli device disconnect wlan0")  # Replace wlan0 with actual interface if needed
        try:
            identifier = device.name.split(" ")[-1]  # Extract GoPro identifier (last 4 digits)
            logger.info(f"Processing GoPro: {identifier}")

            # Connect to GoPro and enable WiFi
            ssid, password, client = await connect_and_enable_wifi(identifier)

            # Connect PC Wifi to GoPro
            connect_to_wifi(ssid, password)
            # await asyncio.sleep(10)  # Allow time for WiFi connection

            # Download media for this GoPro
            
            #ask the date and time for the first camera
            if not selected_date:
                selected_date, start_hour, end_hour=download_selected_media_ask_user()
            #For the rest of the camera use the first user prompt
            else:
                download_selected_media(selected_date, start_hour, end_hour)
            # Disconnect BLE
            logger.info(f"Disconnecting GoPro {identifier}...")
            await client.disconnect()
        
        except Exception as e:
            logger.error(f"Error processing GoPro {identifier}: {e}")

import nest_asyncio
nest_asyncio.apply()  # Apply a patch to allow nested event loops

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to GoPro, enable WiFi, connect to WiFi, and download media of selected date.")
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
