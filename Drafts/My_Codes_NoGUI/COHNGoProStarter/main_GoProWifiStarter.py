import sys
import json
import asyncio
from base64 import b64encode
from pathlib import Path
import requests

from tutorial_modules import logger


import keyboard 

# Global stop event shared by all tasks
stop_event = asyncio.Event()

# Helper to send shutter commands 
async def send_shutter_command(url, headers, certificate, command_name):
    logger.info(f"{command_name} shutter: sending {url}")
    try:
        response = requests.get(
            url,
            timeout=10,
            headers=headers,
            verify=str(certificate)
        )
        response.raise_for_status()
        logger.info(f"Shutter {command_name.lower()} command sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error {command_name.lower()} shutter: {e}")
        return False

# Controls one GoPro camera
async def control_gopro(creds: dict, cert_path: Path):
    ip_address = creds["ip_address"]
    username = creds["username"]
    password = creds["password"]

    auth_token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {auth_token}"}

    shutter_on_url = f"https://{ip_address}/gopro/camera/shutter/start"
    shutter_off_url = f"https://{ip_address}/gopro/camera/shutter/stop"

    if not await send_shutter_command(shutter_on_url, headers, cert_path, "Start"):
        logger.error(f"[{ip_address}] Failed to start shutter.")
        return

    logger.info(f"[{ip_address}] Recording started.")

    try:
        while not stop_event.is_set():
            await asyncio.sleep(0.1)
    finally:
        if not await send_shutter_command(shutter_off_url, headers, cert_path, "Stop"):
            logger.error(f"[{ip_address}] Failed to stop shutter.")
        else:
            logger.info(f"[{ip_address}] Recording stopped.")

# Task to monitor keyboard for spacebar press and trigger stop_event
async def wait_for_spacebar():
    if not keyboard:
        logger.warning("keyboard module not available. Cannot detect keypress.")
        return

    logger.info("Press SPACEBAR to stop all recordings...")

    # Use a thread-safe event to coordinate between keyboard hook and async code
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def on_space(event):
        if event.event_type == 'down' and event.name == 'space':
            logger.info("Spacebar pressed. Stopping recordings.")
            if not future.done():
                loop.call_soon_threadsafe(future.set_result, True)

    keyboard.hook(on_space)

    try:
        await future  # Wait until spacebar pressed
        stop_event.set()
    finally:
        keyboard.unhook(on_space)

# Main multi-camera orchestration
async def main():
    certs_dir = Path("./certifications")
    creds_file = certs_dir / "gopro_credentials.txt"

    if not creds_file.exists():
        logger.error("gopro_credentials.txt not found.")
        sys.exit(1)

    with open(creds_file, "r") as f:
        chunks = f.read().strip().split("\n\n")

    tasks = []
    for chunk in chunks:
        try:
            creds = json.loads(chunk)
            identifier = creds.get("identifier", "unknown")
            cert_path = Path(f"certifications/GoPro_{identifier}_cohn.crt")
            tasks.append(control_gopro(creds, cert_path))
        except json.JSONDecodeError as e:
            logger.error(f"Skipping invalid credential block: {e}")

    # Add keyboard listener task
    tasks.append(wait_for_spacebar())

    await asyncio.gather(*tasks)

# Entrypoint
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
