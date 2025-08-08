import sys
import asyncio
import os
import requests
import json
from base64 import b64encode
from pathlib import Path
from datetime import datetime
import subprocess
import re

from tutorial_modules import logger

async def send_authenticated_request(
    url: str,
    headers: dict,
    certificate: Path,
    method: str = "GET",
    stream: bool = False,
    data: dict = None,
    is_json_response: bool = True
):
    logger.debug(f"Sending {method} request to: {url}")
    try:
        if method.upper() == "GET":
            response = requests.get(
                url, timeout=10, headers=headers, verify=str(certificate), stream=stream
            )
        elif method.upper() == "POST":
            response = requests.post(
                url, timeout=10, headers=headers, verify=str(certificate), json=data
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        if is_json_response:
            return response.json()
        elif stream:
            return response
        else:
            return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to {url}: {e}")
        raise

async def get_media_list_cohn(ip_address: str, headers: dict, certificate: Path) -> list[tuple[str, datetime]]:
    media_list_url = f"https://{ip_address}/gopro/media/list"
    logger.info(f"Fetching media list from {media_list_url}")

    try:
        media_json = await send_authenticated_request(media_list_url, headers, certificate)
        media_data = []

        for media_item in media_json.get('media', []):
            folder_name = media_item.get('d')
            for file_info in media_item.get('fs', []):
                file_name = file_info.get('n')
                creation_timestamp = file_info.get('cre')

                if creation_timestamp is not None:
                    try:
                        file_timestamp = datetime.fromtimestamp(int(creation_timestamp))
                        media_data.append((f"{folder_name}/{file_name}", file_timestamp))
                    except Exception as e:
                        logger.warning(f"Error parsing timestamp for {file_name}: {e}")

        for full_path, dt in media_data:
            print(f"https://{ip_address}/videos/DCIM/{full_path} ({dt.strftime('%d-%b-%Y %H:%M:%S')})")

        return media_data

    except Exception as e:
        logger.error(f"Failed to get media list: {e}")
        return []

def prompt_user_for_date_range(media_data):
    unique_dates = sorted(set(dt.strftime("%d-%b-%Y") for _, dt in media_data))
    if not unique_dates:
        logger.info("No media files found.")
        sys.exit(0)

    print("\nAvailable video dates:")
    for idx, date in enumerate(unique_dates, 1):
        print(f"{idx}. {date}")

    while True:
        try:
            choice = int(input("\nEnter the number corresponding to the date you want to download: "))
            if 1 <= choice <= len(unique_dates):
                selected_date = unique_dates[choice - 1]
                break
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")

    all_day = input(f"Download all videos for {selected_date}? (y/n): ").strip().lower()
    if all_day == 'y':
        return selected_date, None, None

    start_time = input("Start time (HH:MM): ").strip()
    end_time = input("End time (HH:MM): ").strip()
    return selected_date, start_time, end_time

def get_creation_time(file_path: str) -> str:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error: {result.stderr}")

    meta = json.loads(result.stdout)

    for stream in meta.get("streams", []):
        tags = stream.get("tags", {})
        if "creation_time" in tags:
            return tags["creation_time"]

    return meta.get("format", {}).get("tags", {}).get("creation_time")

async def download_file_cohn(
    identifier: str,
    ip_address: str,
    headers: dict,
    certificate: Path,
    file_path: str,
    output_dir: str = "downloads"
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    match = re.search(r'(GX\d{6})\.\w+$', os.path.basename(file_path), re.IGNORECASE)
    gopro_file_identifier = match.group(1).upper() if match else None

    if gopro_file_identifier:
        for existing_file in os.listdir(output_dir):
            if gopro_file_identifier in existing_file:
                logger.info(f"Skipping {file_path}: {gopro_file_identifier} already exists as {existing_file}")
                return

    file_url = f"https://{ip_address}/videos/DCIM/{file_path}"
    temp_local_path = os.path.join(output_dir, os.path.basename(file_path))

    logger.info(f"Downloading {file_path} from {file_url} to {temp_local_path}")

    try:
        response_stream = await send_authenticated_request(
            file_url, headers, certificate, method="GET", stream=True, is_json_response=False
        )

        with open(temp_local_path, "wb") as f:
            for chunk in response_stream.iter_content(chunk_size=8192):
                f.write(chunk)

        creation_time = get_creation_time(temp_local_path)
        if creation_time:
            dt_obj = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            original_filename_part = os.path.splitext(os.path.basename(temp_local_path))[0]
            gopro_id_in_original = re.search(r'(GX\d{6})', original_filename_part, re.IGNORECASE)
            
            if gopro_id_in_original:
                new_name = f"{dt_obj.strftime('%Y%m%d_%H%M%S')}-GoPro{identifier}-{gopro_id_in_original.group(1).upper()}{Path(temp_local_path).suffix}"
            else:
                new_name = f"{dt_obj.strftime('%Y%m%d_%H%M%S')}-GoPro{identifier}-{os.path.basename(temp_local_path)}"

            final_path = os.path.join(output_dir, new_name)
            os.rename(temp_local_path, final_path)
            logger.info(f"Renamed to: {final_path}")
        else:
            logger.warning("No creation_time found; file left as-is.")

    except Exception as e:
        logger.error(f"Failed to download {file_path}: {e}")

async def download_from_camera(creds: dict, cert_path: Path, selected_date: str = None, start_time: str = None, end_time: str = None, output_dir: str = "downloads"):
    identifier = creds["identifier"]
    ip_address = creds["ip_address"]
    username = creds["username"]
    password = creds["password"]

    auth_token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {auth_token}"}

    try:
        media_data = await get_media_list_cohn(ip_address, headers, cert_path)
        if not media_data:
            logger.warning(f"[{ip_address}] No media found.")
            return

        files_to_download = []
        for file_path, timestamp in media_data:
            if selected_date:
                if timestamp.strftime("%d-%b-%Y") != selected_date:
                    continue
                if start_time and end_time:
                    file_time = timestamp.strftime("%H:%M")
                    if not (start_time <= file_time <= end_time):
                        continue
            files_to_download.append(file_path)

        if not files_to_download:
            logger.info(f"[{ip_address}] No media files to download.")
            return

        logger.info(f"[{ip_address}] Downloading {len(files_to_download)} files...")
        for file_path in files_to_download:
            await download_file_cohn(identifier, ip_address, headers, cert_path, file_path, output_dir=output_dir)
    except Exception as e:
        logger.error(f"[{ip_address}] Error downloading media: {e}")

async def main():
    output_dir = "./downloads"
    certs_dir = Path("./certifications")
    creds_file = certs_dir / "gopro_credentials.txt"

    if not creds_file.exists():
        logger.error("gopro_credentials.txt not found.")
        sys.exit(1)

    with open(creds_file, "r") as f:
        chunks = f.read().strip().split("\n\n")

    camera_configs = []

    for chunk in chunks:
        try:
            creds = json.loads(chunk)
            identifier = creds.get("identifier", "unknown")
            cert_path = certs_dir / f"GoPro_{identifier}_cohn.crt"
            camera_configs.append((creds, cert_path))
        except json.JSONDecodeError as e:
            logger.error(f"Skipping invalid credential block: {e}")
        except Exception as e:
            logger.error(f"Error processing camera: {e}")

    if not camera_configs:
        logger.warning("No valid camera configurations found.")
        return

    selected_date = None
    start_time = None
    end_time = None

    for i, (creds, cert_path) in enumerate(camera_configs):
        ip_address = creds["ip_address"]
        identifier = creds["identifier"]
        auth_token = b64encode(f"{creds['username']}:{creds['password']}".encode("utf-8")).decode("ascii")
        headers = {"Authorization": f"Basic {auth_token}"}

        if i == 0:
            media_data = await get_media_list_cohn(ip_address, headers, cert_path)
            if not media_data:
                logger.warning(f"[{ip_address}] No media to select from.")
                continue
            selected_date, start_time, end_time = prompt_user_for_date_range(media_data)

        await download_from_camera(creds, cert_path, selected_date, start_time, end_time, output_dir=output_dir)

import nest_asyncio
nest_asyncio.apply()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
