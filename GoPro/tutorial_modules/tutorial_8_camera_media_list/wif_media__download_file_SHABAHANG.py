# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 15:33:54 2025

@author: sshayeng-admin
"""

import sys
import argparse
import requests
import re
import os 
from bs4 import BeautifulSoup
from tutorial_modules import logger

GOPRO_BASE_URL = "http://10.5.5.9/videos/DCIM/100GOPRO/"
def get_media_list():
    """Scrape the GoPro media directory and extract available files."""
    logger.info(f"Fetching media list from {GOPRO_BASE_URL}")
    
    response = requests.get(GOPRO_BASE_URL, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    media_files = []

    # Find all links in the directory listing
    for link in soup.find_all('a', href=True):
        file_path = link['href']  # Full relative path like /videos/DCIM/100GOPRO/filename.mp4
        file_name = os.path.basename(file_path)  # Extract only filename

        if file_name.lower().endswith(('.mp4', '.jpg', '.lrv')):  # Adjust as needed
            media_files.append(file_name)

    if not media_files:
        raise RuntimeError("No media files found on the GoPro storage")

    logger.info(f"Found {len(media_files)} files.")
    return media_files


def download_file(file_name):
    """Download a specific file from the GoPro."""
    file_url = GOPRO_BASE_URL + file_name
    logger.info(f"Downloading {file_name} from {file_url}")

    with requests.get(file_url, stream=True, timeout=10) as request:
        request.raise_for_status()
        with open(file_name, "wb") as f:
            logger.info(f"Saving {file_name}...")
            for chunk in request.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    media_files = get_media_list()

    # Example: Download only MP4 files
    for file in media_files:
        if file.lower().endswith('.mp4'):
            download_file(file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files from GoPro storage.")
    parser.parse_args()

    try:
        main()
    except Exception as e:
        logger.error(e)
        sys.exit(-1)
    else:
        sys.exit(0)
