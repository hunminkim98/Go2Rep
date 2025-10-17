import sys
import json
import asyncio
from pathlib import Path
from tutorial_modules import logger
import requests
from base64 import b64encode

# ========== Helper Function to Send Camera Setting Command ==========

def set_camera_setting(ip_address, setting_id, value, headers=None, certificate=None):
    url = f"https://{ip_address}/gopro/camera/setting"
    params = {
        "setting": setting_id,
        "option": value
    }
    logger.info(f"Setting ID {setting_id} to option {value} on {ip_address}")
    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers=headers,
            verify=str(certificate) if certificate else True  # Pass cert or default to True
        )
        response.raise_for_status()
        logger.info(f"Successfully set setting {setting_id} to {value}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to set setting {setting_id} to {value} on {ip_address}: {e}")
        return False


def load_preset(ip_address, preset_id, headers=None, certificate=None):
    url = f"https://{ip_address}/gopro/camera/presets/load"
    params = {
        "id": preset_id
    }
    logger.info(f"Loading preset {preset_id} on {ip_address}")
    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers=headers,
            verify=str(certificate) if certificate else True
        )
        response.raise_for_status()
        logger.info(f"Successfully loaded preset {preset_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to load preset {preset_id} on {ip_address}: {e}")
        return False 
    
    
async def configure_gopro(creds: dict, resolution_id: int, fps_id: int):
    ip_address = creds["ip_address"]
    username = creds["username"]
    password = creds["password"]
    identifier = creds.get("identifier", "unknown")
    cert_path = Path(f"certifications/GoPro_{identifier}_cohn.crt")

    auth_token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {auth_token}"}

    logger.info(f"Configuring GoPro at {ip_address}...")

    if resolution_id==12 or resolution_id==38: 
        # Step 0: Load Preset ID (standard/default)
        success_preset = load_preset(ip_address, 1, headers, cert_path)
    else:
        success_preset = load_preset(ip_address, 0, headers, cert_path)

    # Step 2: Set resolution
    success_res = set_camera_setting(ip_address, 2, resolution_id, headers, cert_path)

    # Step 3: Set FPS
    success_fps = set_camera_setting(ip_address, 234, fps_id, headers, cert_path)

    if success_res and success_fps and success_preset:
        logger.info(f"[{ip_address}] Configuration successful.")
    else:
        logger.warning(f"[{ip_address}] Configuration failed.")
# ========== Main Async Orchestration ==========

async def main():
    certs_dir = Path("./certifications")
    creds_file = certs_dir / "gopro_credentials.txt"

    if not creds_file.exists():
        logger.error("gopro_credentials.txt not found.")
        sys.exit(1)

    # Ask user for resolution
    print("Supported Resolutions:")
    print(" 1: 4K\n 4: 2.7K\n 9: 1080p\n 12: GoPro13 720p,400\n 38: GoPro13 900p,360")
    resolution_id = int(input("Enter the resolution ID: "))

    # Ask user for FPS
    print("Supported FPS:")
    print(" 0: 240\n 1: 120\n 5: 60\n 8:GoPro13 30\n 10:GoPro13 24 ")
    fps_id = int(input("Enter the FPS ID: "))

    with open(creds_file, "r") as f:
        chunks = f.read().strip().split("\n\n")

    tasks = []
    for chunk in chunks:
        try:
            creds = json.loads(chunk)
            tasks.append(configure_gopro(creds, resolution_id, fps_id))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid credential block: {e}")

    await asyncio.gather(*tasks)

# ========== Entrypoint ==========

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
