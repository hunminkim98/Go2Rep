import asyncio
from bleak import BleakClient, BleakScanner
from tutorial_modules import connect_ble, logger, GoProUuid
from tkinter import ttk, messagebox
import tkinter as tk
import subprocess
import re
from bleak.backends.characteristic import BleakGATTCharacteristic
import platform
import os
import time
import tempfile
from bleak.backends.device import BLEDevice as BleakDevice

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


def get_saved_wifi_profiles():
    output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='utf-8')
    # Determine language pattern based on content
    if "All User Profile" in output:
        # English Windows
        pattern = r"All User Profile\s*:\s(.*)"
    elif "Profil Tous les utilisateurs" in output:
        # French Windows
        pattern = r"Profil Tous les utilisateurs\s*:\s(.*)"
    else:
        raise RuntimeError("Unsupported language in 'netsh' output. Cannot parse Wi-Fi profiles.")
    profiles = re.findall(pattern, output)
    return [profile.strip() for profile in profiles]

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
    
def connect_to_wifi(ssid: str, password: str, retries: int = 10, delay: int = 5):
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
                time.sleep(5)
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
            time.sleep(5)

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


async def main(gopro_list, identifier=None, timeout=None):
   # Check wifis of this device
   #  logger.info("Fetching saved Wi-Fi profiles and passwords...\n")
    WiFi_profiles = get_saved_wifi_profiles()
    
    if not WiFi_profiles:
        logger.info("No saved Wi-Fi profiles found.")
        return

    # for profile in profiles:
    #     password = get_wifi_password(profile)
    #     logger.info(f"SSID: {profile}\nPassword: {password}\n{'-'*30}")
    
    # Detect all available GoPros
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
                    return await main(gopro_list)
                elif response is None:
                    logger.error("ERROR: User aborted due to missing GoPros.")
                    raise RuntimeError("User aborted due to missing GoPros.")
                    
    print(f"Devices are: {matched_devices}")
    if not matched_devices:
        print("No GoPro cameras found.")
        return

    print(f"Found {len(matched_devices)} GoPro cameras:")
    # Iterate over matched GoPro devices
    # Print matched GoPro devices
    existing_GoPro_profiles = []
    All_GoPro_Profiles=[]
    newly_added_GoPro_profiles = []
    Failed_GoPros=[]
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
            except Exception as e:
                success=0
                logger.warning(f"{e}")  
                Failed_GoPros.append((device.name))
                continue
            # Skip if SSID already in WiFi profiles
            if ssid in WiFi_profiles:
                logger.info(f"GoPro WiFi SSID '{ssid}' is already registered with password '{password}'. Skipping camera.")
                existing_GoPro_profiles.append((device.name, ssid, password))
                All_GoPro_Profiles.append((device.name, ssid, password ))
                await client.disconnect()
                continue
            # Connect PC Wifi to GoPro
            try:
                success=connect_to_wifi(ssid, password)
            except Exception as e:
                success=0
                logger.warning(f"{e}")  
                Failed_GoPros.append((device.name))
                continue
            # Disconnect BLE
            if success:
                newly_added_GoPro_profiles.append((device.name, ssid, password))
                All_GoPro_Profiles.append((device.name, ssid, password ))
            else:
                Failed_GoPros.append(device.name)
            logger.info(f"Disconnecting GoPro {identifier}...")
            await client.disconnect()
            
        except Exception as e:
            logger.error(f"Error processing GoPro {identifier}: {e}")

            
        
    logger.info(f"\nSummary of Wi-Fi Profile Status:")
    
    logger.info(f"\n✅ Existing Profiles ({len(existing_GoPro_profiles)}):")
    for name, ssid, password in existing_GoPro_profiles:
        logger.info(f"- {name}: {ssid}")
    
    logger.info(f"\n➕ Newly Added Profiles ({len(newly_added_GoPro_profiles)}):")
    for name, ssid, password in newly_added_GoPro_profiles:
        logger.info(f"- {name}: {ssid}")        
        
    return All_GoPro_Profiles, Failed_GoPros
    
    
