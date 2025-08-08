# Go2Rep/tools/gopro_capture_GP13.py

import sys
import json
import asyncio
from pathlib import Path
from base64 import b64encode
import requests
import keyboard

from tutorial_modules import logger

stop_event = asyncio.Event()
tasks = []

def reset_stop_event():
    global stop_event
    stop_event = asyncio.Event()

async def send_shutter_command(url, headers, certificate, command_name):
    logger.info(f"{command_name} shutter: sending {url}")
    try:
        response = requests.get(url, timeout=10, headers=headers, verify=str(certificate))
        response.raise_for_status()
        logger.info(f"Shutter {command_name.lower()} command sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error {command_name.lower()} shutter: {e}")
        return False

async def control_gopro(creds: dict, cert_path: Path):
    ip_address = creds["ip_address"]
    username = creds["username"]
    password = creds["password"]

    auth_token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {auth_token}"}

    shutter_on_url = f"https://{ip_address}/gopro/camera/shutter/start"
    shutter_off_url = f"https://{ip_address}/gopro/camera/shutter/stop"

    if not await send_shutter_command(shutter_on_url, headers, cert_path, "Start"):
        return

    try:
        while not stop_event.is_set():
            await asyncio.sleep(0.1)
    finally:
        await send_shutter_command(shutter_off_url, headers, cert_path, "Stop")

async def load_gopro_tasks(certs_dir: Path):
    # certs_dir = Path("./certifications")
    creds_file = certs_dir / "gopro_credentials.txt"

    if not creds_file.exists():
        raise FileNotFoundError("gopro_credentials.txt not found")

    with open(creds_file, "r") as f:
        chunks = f.read().strip().split("\n\n")
    gopro_tasks = []
    for chunk in chunks:
        creds = json.loads(chunk)
        identifier = creds.get("identifier", "unknown")
        cert_path = Path(f"certifications/GoPro_{identifier}_cohn.crt")
        gopro_tasks.append(control_gopro(creds, cert_path))

    return gopro_tasks

async def wait_for_spacebar():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def on_space(event):
        if event.event_type == 'down' and event.name == 'space':
            logger.info("Spacebar pressed. Stopping recordings.")
            if not future.done():
                loop.call_soon_threadsafe(future.set_result, True)

    keyboard.hook(on_space)

    try:
        await future
        stop_event.set()
    finally:
        keyboard.unhook(on_space)

async def start_gopro13_capture(certs_dir: Path):
    reset_stop_event()
    global tasks
    tasks = await load_gopro_tasks(certs_dir)
    tasks.append(wait_for_spacebar())
    async def safe_gather():
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Unhandled exception in tasks: {e}")
    
    asyncio.create_task(safe_gather())

def stop_gopro13_capture():
    stop_event.set()
