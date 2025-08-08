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

async def run_gopro13_configuration(fps_GUI: int, resolution_GUI: int, certs_dir: Path):
    # certs_dir = Path("./certifications")
    creds_file = certs_dir / "gopro_credentials.txt"

    if not creds_file.exists():
        logger.error("gopro_credentials.txt not found.")
        sys.exit(1)
    
    # Ask user for resolution
    
    # Resolution and FPS mappings
    RESOLUTION_MAP = {
        "4000": 1,
        "2700": 4,
        "1080": 9,
        "GP13-720p,400": 12,
        "GP13-900p,360": 38,
    }
    
    FPS_MAP = {
        "240": 0,
        "120": 1,
        "60": 5,
        "GP13-30": 8,
        "GP13-24": 10,
    }

    resolution_id = RESOLUTION_MAP.get(str(resolution_GUI))
    fps_id = FPS_MAP.get(str(fps_GUI))

    if resolution_id is None:
        logger.error(f"Unsupported resolution: {resolution_GUI}")
        sys.exit(1)

    if fps_id is None:
        logger.error(f"Unsupported FPS: {fps_GUI}")
        sys.exit(1)

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

# if __name__ == "__main__":
#     import nest_asyncio
#     nest_asyncio.apply()
#     asyncio.run(main())
