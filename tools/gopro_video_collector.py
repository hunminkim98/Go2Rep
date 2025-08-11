# gopro_video_collector.py
# -*- coding: utf-8 -*-
"""
Connect to GoPro via BLE, enable WiFi, connect to WiFi, and download selected media by date.
"""
import sys
import os
import asyncio
import time
import platform
import requests
import subprocess
from datetime import datetime
import tempfile
from tkinter import ttk, messagebox
import tkinter as tk
import re
from pathlib import Path
import json
from bleak.backends.device import BLEDevice as BleakDevice
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bs4 import BeautifulSoup


import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from tutorial_modules import GoProUuid, logger, connect_ble

GOPRO_BASE_URL = "http://10.5.5.9/videos/DCIM/100GOPRO/"
GOPRO_BASE_URL_2Download = "http://10.5.5.9"


def create_wifi_profile_xml(ssid: str, password: str) -> str:
    return f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>manual</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""

def connect_to_wifi_windows(ssid: str, password: str):
    xml_profile = create_wifi_profile_xml(ssid, password)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as temp:
        temp.write(xml_profile.encode("utf-8"))
        temp_path = temp.name

    os.system(f'netsh wlan add profile filename="{temp_path}" interface="Wi-Fi"')
    os.system(f'netsh wlan connect name="{ssid}" ssid="{ssid}" interface="Wi-Fi"')
    os.remove(temp_path)

async def scan_bluetooth_devices():
    matched_devices = []
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name and "GoPro" in device.name:
            matched_devices.append(device)
    return matched_devices


def is_connected_to_wifi(target_ssid: str | None = None) -> bool:
    """
    Check if the PC is connected to a WiFi network.
    Optionally verify if connected to a specific SSID.
    """
    if os.name == "nt":  # Windows
        try:
            output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8")
            ssid_match = re.search(r"^\s*SSID\s*:\s(.*)$", output, re.MULTILINE)
            if not ssid_match:
                return False  # Not connected
            current_ssid = ssid_match.group(1).strip()
            if target_ssid:
                return current_ssid == target_ssid
            return True
        except subprocess.CalledProcessError:
            return False
    else:  # Linux/macOS
        try:
            output = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], encoding="utf-8")
            for line in output.strip().split('\n'):
                if line.startswith("yes:"):
                    current_ssid = line.split(":")[1]
                    if target_ssid:
                        return current_ssid == target_ssid
                    return True
            return False
        except subprocess.CalledProcessError:
            return False


def get_available_networks():
    """Scan and return a list of available WiFi SSIDs."""
    networks = []
    if os.name == "nt":
        output = subprocess.run(["netsh", "wlan", "show", "network"], capture_output=True, text=True).stdout
        # logger.info(output)
        networks = [line.split(":")[1].strip() for line in output.split("\n") if "SSID" in line]
    else:
        output = subprocess.run(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], capture_output=True, text=True).stdout
        # logger.info(output)
        networks = output.split("\n")
    return [ssid for ssid in networks if ssid]


def get_wifi_password(profile_name):
    try:
        profile_info = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile_name, 'key=clear'], encoding='utf-8')
        password = re.search(r"Key Content\s*:\s(.*)", profile_info)
        return password.group(1).strip() if password else "N/A"
    except subprocess.CalledProcessError:
        return "Error retrieving"
    
def show_manual_connect_message(ssid, password, trial):
    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(password)
        root.update()  # Keep clipboard after window closes
        copy_btn.config(text="Copied!", state="disabled")

    def close_window():
        root.destroy()

    root = tk.Tk()
    root.title("Wi-Fi Connection Help")
    root.geometry("400x300")
    root.resizable(False, False)

    msg = (
        f"After {trial} attempts, connection to Wi-Fi '{ssid}' failed.\n\n"
        "Please click the Wi-Fi icon in the taskbar to check available networks.\n"
        "Try to refresh and look for the SSID below.\n\n"
        f"SSID: {ssid}\nPassword: {password}\n\n"
        "You can connect manually (can be helpful).\n"
        "Once finished, click OK to continue."
    )

    label = tk.Label(root, text=msg, wraplength=380, justify="left")
    label.pack(pady=10, padx=10)

    copy_btn = tk.Button(root, text="Copy Password", command=copy_to_clipboard)
    copy_btn.pack(pady=5)

    ok_btn = tk.Button(root, text="OK", command=close_window)
    ok_btn.pack(pady=5)

    root.mainloop()
    
def connect_to_wifi(ssid: str, password: str, retries: int = 10, delay: int = 15):
    logger.info(f"Connecting to WiFi: {ssid}, password: {password}")
    attempt = 0
    while attempt < retries:
        attempt += 1
        available_networks = get_available_networks()
        logger.info(f"Attempt {attempt}/{retries} to connect to '{ssid}'")
        if ssid not in available_networks:
            logger.warning(f"Wi-Fi '{ssid}' not found. ")
            logger.warning("Click the Wi-Fi icon in the taskbar to check available networks")
            logger.warning("be closer to the gopro for better signal")
            time.sleep(2)
            if attempt in [3, 6]:
                logger.info("a pop-window appeared! It might be hidden behind the GUI")
                show_manual_connect_message(ssid, password, attempt)
                time.sleep(3)
            continue  # Retry
        if os.name == "nt":
            connect_to_wifi_windows(ssid, password)
        else:
            os.system(f'nmcli device wifi connect "{ssid}" password "{password}"')
        time.sleep(2)

        if is_connected_to_wifi(ssid):
            logger.info("Successfully connected to Wi-Fi!")
            success=1
            time.sleep(delay)
            return success
        
        logger.warning(f"Wi-Fi connection failed on attempt {attempt}. Retrying...")
        if attempt in [3, 6]:
            logger.info("a pop-window appeared! It might be hidden behind the GUI")
            show_manual_connect_message(ssid, password, attempt)    
            time.sleep(3)

    logger.error(f"Failed to connect to Wi-Fi '{ssid}' after {retries} attempts.")
    success=0
    return success    

async def connect_and_enable_wifi(identifier: str | None = None, device: BleakDevice | None = None) -> tuple[str, str, BleakClient]:
    event = asyncio.Event()
    client: BleakClient

    async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
        logger.info(f'Received response at {uuid}: {data.hex(":")}')
        event.set()

    if device:
        # Monkey-patch BleakScanner.discover to return only the known device
        original_discover = BleakScanner.discover
        async def fake_discover(*args, **kwargs):
            return [device]
        BleakScanner.discover = fake_discover
    try:
        client = await connect_ble(notification_handler, identifier)
    finally:
        if device:
            # Restore the original discover method
            BleakScanner.discover = original_discover

    ssid = (await client.read_gatt_char(GoProUuid.WIFI_AP_SSID_UUID.value)).decode()
    password = (await client.read_gatt_char(GoProUuid.WIFI_AP_PASSWORD_UUID.value)).decode()

    logger.info("Enabling WiFi AP")
    event.clear()
    request = bytes([0x03, 0x17, 0x01, 0x01])
    await client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, request, response=True)
    await event.wait()
    logger.info("WiFi AP enabled")

    return ssid, password, client

def get_media_list(formats=None): 
    logger.info(f"Fetching media list from {GOPRO_BASE_URL}")
    response = requests.get(GOPRO_BASE_URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    media_data = []
    for row in soup.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) >= 2:
            link = columns[0].find('a', href=True)
            date_text = columns[1].get_text(strip=True)
            
            if link and date_text and date_text != "-":
                try:
                    dt = datetime.strptime(date_text, "%d-%b-%Y %H:%M")
                    date_only = dt.strftime("%d-%b-%Y")
                    hour_only = dt.strftime("%H:%M")
                    file_extension = os.path.splitext(link['href'])[1].upper()
                    if formats is None or file_extension in formats:
                        media_data.append((link['href'], date_only, hour_only))
                except ValueError:
                    logger.warning(f"Skipping file due to unexpected date format: {date_text}")

    return media_data




# def gui_prompt_user_for_date_and_time(media_data, root):
#     result = {"date": None, "start": None, "end": None}
#     root = tk._default_root
#     if not root:
#         root = tk.Tk()
#         root.withdraw()
#     # Extract unique dates
#     unique_dates = sorted(set(date for _, date, _ in media_data))

#     if not unique_dates:
#         messagebox.showinfo("No Media", "No video files found on the GoPro.")
#         return None, None, None

#     popup = tk.Toplevel(root)
#     popup.title("Videos from the following dates were found on this GoPro. Select Video Date and Time Range")
#     popup.geometry("350x250")
#     popup.transient(root)
#     popup.grab_set()

#     ttk.Label(popup, text="Select Date:").pack(pady=(10, 5))
#     selected_date = tk.StringVar()
#     date_box = ttk.Combobox(popup, textvariable=selected_date, values=unique_dates, state="readonly")
#     date_box.pack(pady=5)

#     # Checkbox to enable time range
#     use_time_range = tk.BooleanVar(value=False)
#     time_check = ttk.Checkbutton(popup, text="Specify Time Range (Optional)", variable=use_time_range)
#     time_check.pack(pady=(10, 5))

#     time_frame = tk.Frame(popup)
#     time_frame.pack(pady=5)

#     ttk.Label(time_frame, text="Start (HH:MM):").grid(row=0, column=0, padx=5)
#     start_entry = ttk.Entry(time_frame, width=10)
#     start_entry.grid(row=0, column=1)

#     ttk.Label(time_frame, text="End (HH:MM):").grid(row=1, column=0, padx=5)
#     end_entry = ttk.Entry(time_frame, width=10)
#     end_entry.grid(row=1, column=1)

#     def on_ok():
#         result["date"] = selected_date.get()
#         if use_time_range.get():
#             result["start"] = start_entry.get().strip()
#             result["end"] = end_entry.get().strip()
#         popup.destroy()

#     ttk.Button(popup, text="OK", command=on_ok).pack(pady=15)
#     popup.wait_window()

#     return result["date"], result["start"], result["end"]


# def get_creation_time(file_path: str) -> str:
#     cmd = [
#         "ffprobe", "-v", "quiet", "-print_format", "json",
#         "-show_format", "-show_streams", file_path
#     ]
#     result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     if result.returncode != 0:
#         raise RuntimeError(f"ffprobe error: {result.stderr}")

#     meta = json.loads(result.stdout)

#     for stream in meta.get("streams", []):
#         tags = stream.get("tags", {})
#         if "creation_time" in tags:
#             return tags["creation_time"]

#     return meta.get("format", {}).get("tags", {}).get("creation_time")


def download_file(file_name,destination_path):
    file_url = f"{GOPRO_BASE_URL_2Download}{file_name}"
    logger.info(f"Downloading {file_name} from {file_url}")

    # directory = os.path.dirname(file_name)
    # if not os.path.exists(directory):
    #     os.makedirs(directory)
    
    with requests.get(file_url, stream=True, timeout=10) as request:
        request.raise_for_status()
        with open(destination_path, "wb") as f:
            for chunk in request.iter_content(chunk_size=8192):
                f.write(chunk)
    
    logger.info(f"Downloaded file saved to {destination_path}")

# def download_selected_media_ask_user(Video_Source_folder):
#     # This function is used only for the first camera
#     file_formats = ['.MP4']  # Add more formats if needed  
#     media_files = get_media_list(formats=file_formats)
    
#     if not media_files:
#         logger.info("No media files found on the GoPro.")
#         return

#     from tkinter import _default_root  # You can pass root explicitly too if you prefer

#     selected_date, start_hour, end_hour = gui_prompt_user_for_date_and_time(media_files, _default_root)
    
#     # Filter videos based on selected date and time range
#     if start_hour and end_hour:
#         files_to_download = [
#             file for file, date, hour in media_files
#             if date == selected_date and start_hour <= hour <= end_hour
#         ]
#     else:
#         files_to_download = [
#             file for file, date, _ in media_files
#             if date == selected_date
#         ]

#     if not files_to_download:
#         logger.info(f"No videos found for {selected_date}.")
#         return

#     logger.info(f"Downloading videos for {selected_date}...")
#     for file in files_to_download:
#         base_name = os.path.basename(file)
#         destination_path = os.path.join(Video_Source_folder, base_name)

#         if not os.path.exists(destination_path):
#             download_file(file, destination_path)
#         else:
#             print(f"File already exists: {destination_path}, skipping download.")
        
#    return selected_date, start_hour, end_hour


def download_selected_media(selected_date, start_hour, end_hour, Video_Source_folder,filename_convention, identifier):
    # This function is used for second, third, etc... camera
    file_formats = ['.MP4']  # Add more formats if needed    
    media_files = get_media_list(formats=file_formats)
    filesFound=1
    if not media_files:
        logger.info("No media files found on the GoPro.")
        filesFound=0
        return filesFound

    # Filter videos based on selected date and time range
    if start_hour and end_hour:
        files_to_download = [
            file for file, date, hour in media_files
            if datetime.strptime(date, "%d-%b-%Y").strftime("%Y-%m-%d") == selected_date and start_hour <= hour <= end_hour
        ]
    else:
        files_to_download = [
            file for file, date, _ in media_files
            if datetime.strptime(date, "%d-%b-%Y").strftime("%Y-%m-%d") == selected_date
        ]

    if not files_to_download:
        logger.info(f"No videos found for {selected_date}.")
        filesFound=0
        return filesFound
    
    logger.info(f"Downloading videos for {selected_date}...")
    if filename_convention==2:
        for file in files_to_download:
            base_name = os.path.basename(file)
            destination_path = os.path.join(Video_Source_folder, base_name)
    
            if not os.path.exists(destination_path):
                download_file(file, destination_path)
            else:
                print(f"File already exists: {destination_path}, skipping download.")
    elif filename_convention == 1:
        for file in files_to_download:
            base_name = os.path.basename(file)
            match = re.search(r'(GX\d{6})\.\w+$', base_name, re.IGNORECASE)
            gopro_file_identifier = match.group(1).upper() if match else None
    
            # Refined existence check
            already_exists = False
            if gopro_file_identifier:
                for existing_file in os.listdir(Video_Source_folder):
                    if gopro_file_identifier in existing_file and f"GoPro{identifier}" in existing_file:
                        logger.info(f"Skipping {file}: already exists as {existing_file}")
                        already_exists = True
                        break
    
            if already_exists:
                continue
    
            # Download file
            temp_path = os.path.join(Video_Source_folder, base_name)
            download_file(file, temp_path)

            # Rename using metadata
            # creation_time = get_creation_time(temp_path) #The Hous is the UTC+00 hour GreenWich 
            # if creation_time:
            #     dt_obj = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            #     if gopro_file_identifier:
            #         new_name = f"{dt_obj.strftime('%Y%m%d_%H%M%S')}-GoPro{identifier}-{gopro_file_identifier}{Path(temp_path).suffix}"
            #     else:
            #         new_name = f"{dt_obj.strftime('%Y%m%d_%H%M%S')}-GoPro{identifier}-{base_name}"
            #     final_path = os.path.join(Video_Source_folder, new_name)
            #     os.rename(temp_path, final_path)
            #     logger.info(f"Renamed to: {final_path}")
            # else:
            #     logger.warning("No creation_time found; file left as-is.")
                                   
            # ⏱️ Instead of metadata, Rename by getting date + hour from media_files
            matching_entry = next(
                ((f, date_str, hour_str) for f, date_str, hour_str in media_files if gopro_file_identifier in f),
                None
            )
      
            # Try extracting datetime from base_name
            date_time_match = re.match(r'(\d{8})_(\d{6})', base_name)
            if date_time_match:
                # ✅ Extracted from filename
                date_part, time_part = date_time_match.groups()
                dt_obj = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
            else:
                # ❌ Fall back to metadata
                matching_entry = next(
                    ((f, date_str, hour_str) for f, date_str, hour_str in media_files if gopro_file_identifier and gopro_file_identifier in f),
                    None
                )
                if matching_entry:
                    _, date_str, hour_str = matching_entry
                    dt_obj = datetime.strptime(f"{date_str} {hour_str}", "%d-%b-%Y %H:%M")
                    logger.warning(f"Could not extract time from '{base_name}', using metadata hour_str={hour_str}")
                else:
                    logger.warning(f"No time found for '{base_name}', leaving file as-is.")
                    continue
            
            # Rename
            if gopro_file_identifier:
                new_name = f"{dt_obj.strftime('%Y%m%d_%H%M%S')}-GoPro{identifier}-{gopro_file_identifier}{Path(temp_path).suffix}"
            else:
                new_name = f"{dt_obj.strftime('%Y%m%d_%H%M%S')}-GoPro{identifier}-{base_name}"
            
            final_path = os.path.join(Video_Source_folder, new_name)
            os.rename(temp_path, final_path)
            logger.info(f"Renamed to: {final_path}")
            
    return filesFound
    

async def gopro_video_collection_main(gopro_list, selected_date=None, time_range=None, dest_folder="C:\\videos\\DCIM\\Videos", filename_convention=None ):
    os.makedirs(dest_folder, exist_ok=True)
    start_hour, end_hour = time_range if time_range else (None, None)
    
    os.makedirs(dest_folder, exist_ok=True)
    Video_Source_folder=dest_folder
    

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
                logger.info("a pop-window appeared! It might be hidden behind the GUI")
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
                    return await gopro_video_collection_main(gopro_list, selected_date, time_range, dest_folder) 
                elif response is None:
                    logger.error("ERROR: User aborted due to missing GoPros.")
                    raise RuntimeError("User aborted due to missing GoPros.")
         
    print(f"Devices are: {matched_devices}")
    if not matched_devices:
        print("No GoPro cameras found.")
        return

    print(f"Found {len(matched_devices)} GoPro cameras:")        
    # Print matched GoPro devices
    Downloaded_GoPros=[]
    EmptyGoPros=[]
    FailedGoPros=[]
    max_retries = 2   
    for device in matched_devices:
        # Disconnect the PC from the current WiFi       
        if platform.system() == "Windows":
            os.system("netsh wlan disconnect")
        else:
            os.system("nmcli device disconnect wlan0")  # Replace wlan0 with actual interface if needed
        try:
            identifier = device.name.split(" ")[-1]  # Extract GoPro identifier (last 4 digits)
            logger.info(f"Processing GoPro: {identifier}")           
            # Rescan for Bluetooth before continuing
            retry_count = 0
            still_visible = False
            while retry_count < max_retries:
                logger.info(f"Verifying visibility for {device.name} (Attempt {retry_count + 1})...")
                current_devices = await scan_bluetooth_devices()
                current_names = [d.name for d in current_devices]
                if device.name in current_names:
                    still_visible = True
                    logger.info(f"{device.name} is still visible.")
                    break
                retry_count += 1
                await asyncio.sleep(1)

            skip_device = False  # Add this before the while loop
            while not still_visible:
                logger.info("a pop-window appeared! It might be hidden behind the GUI")
                response = messagebox.askyesnocancel(
                    "GoPro Not Found",
                    f"The GoPro '{device.name}' is no longer visible via Bluetooth. The BLE command to activate GoPro Wifi risks to be failed. \n\n"
                    "Do you want to continue anyway?\n\n"
                    "Yes = Continue with WiFi Establishment. Even though it can be risky\n"
                    "No = Retry Bluetooth scan. Going closer to the GoPro might help\n"
                    "Cancel = Skip this GoPro"
                )
                if response is True:
                    logger.warning(f"Continuing with WiFi Establishment for {device.name} despite it not being visible.")
                    break
                elif response is False:
                    logger.info(f"Retrying visibility check for {device.name}...")
                    retry_count = 0
                    while retry_count < max_retries:
                        current_devices = await scan_bluetooth_devices()
                        current_names = [d.name for d in current_devices]
                        if device.name in current_names:
                            still_visible = True
                            logger.info(f"{device.name} is now visible.")
                            break
                        retry_count += 1
                        await asyncio.sleep(1)
                    if still_visible:
                        break
                elif response is None:
                    logger.info(f"Skipping GoPro {device.name} as per user request.")
                    skip_device = True
                    break  # Exit the while loop
            
            if skip_device:
                continue  # Now skip to the next GoPro
                    
            # Connect to GoPro and enable WiFi
            try:
                ssid, password, client = await connect_and_enable_wifi(identifier=identifier, device=device)
                # Connect PC Wifi to GoPro
                success=connect_to_wifi(ssid, password)
            except Exception as e:
                success=0
                logger.warning(f"{e}")  
                FailedGoPros.append((device.name))
                continue
            # await asyncio.sleep(10)  # Allow time for WiFi connection
            
            # Download media for this GoPro
            if success:
                Downloaded_GoPros.append((device.name))
                # if not selected_date:
                #     selected_date, start_hour, end_hour=download_selected_media_ask_user(Video_Source_folder)
                # #For the rest of the camera use the first user prompt
                # else:
                filesFound=download_selected_media(selected_date, start_hour, end_hour, Video_Source_folder,filename_convention, identifier)
                if filesFound==0:
                    EmptyGoPros.append((device.name))
                
            # Disconnect BLE
            logger.info(f"Disconnecting GoPro {identifier}...")
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error processing GoPro {identifier}: {e}")
            
    return Downloaded_GoPros,EmptyGoPros,FailedGoPros


