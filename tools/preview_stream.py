# preview_stream.py
# Open GoPro, Version 2.0 (C) Copyright 2021 GoPro, Inc. (http://gopro.com/OpenGoPro).
# This copyright was auto-generated on Mon Jul 31 17:04:07 UTC 2023

"""Example to start and view a preview stream"""

import argparse
import asyncio
import logging  # Import the logging module
from PIL import Image, ImageTk
from rich.console import Console
import tkinter as tk
import cv2
from open_gopro import WirelessGoPro, constants
from open_gopro.demos.gui.util import display_video_blocking
from open_gopro.logger import setup_logging
from open_gopro.util import add_cli_args_and_parse

console = Console()





def display_video_in_label(source: str, label_widget: tk.Label):
    cap = cv2.VideoCapture(source + "?overrun_nonfatal=1&fifo_size=50000000", cv2.CAP_FFMPEG)
    is_streaming = True  # Flag to control streaming

    def update_frame():
        if not is_streaming:
            cap.release()
            label_widget.config(image='')  # Clear label
            return

        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            label_widget.imgtk = imgtk
            label_widget.config(image=imgtk)
        label_widget.after(10, update_frame)

    def stop_stream():
        nonlocal is_streaming
        is_streaming = False

    update_frame()
    return stop_stream  # Return the cleanup function

async def preview_gopro_stream(identifier: str, label_widget, stop_event: asyncio.Event, port: int = 8554):
    async with WirelessGoPro(identifier) as gopro:
        await gopro.http_command.set_preview_stream(mode=constants.Toggle.DISABLE)
        await gopro.ble_command.set_shutter(shutter=constants.Toggle.DISABLE)
        await gopro.http_command.set_preview_stream(mode=constants.Toggle.ENABLE, port=port)

        stop_stream = display_video_in_label(f"udp://127.0.0.1:{port}", label_widget)

        try:
            while not stop_event.is_set():
                await asyncio.sleep(0.5)
        finally:
            stop_stream()
            await gopro.http_command.set_preview_stream(mode=constants.Toggle.DISABLE)


