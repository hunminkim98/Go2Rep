import sys
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
import nest_asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from tutorial_modules import connect_ble, logger, GoProUuid

nest_asyncio.apply()

class GoProControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GoPro Settings")
        self.root.geometry("300x200")

        self.fps_var = tk.StringVar()
        self.res_var = tk.StringVar()

        ttk.Label(root, text="Select FPS:").pack(pady=5)
        self.fps_menu = ttk.Combobox(root, textvariable=self.fps_var, values=["60", "120", "240"], state="readonly")
        self.fps_menu.pack()

        ttk.Label(root, text="Select Resolution:").pack(pady=5)
        self.res_menu = ttk.Combobox(root, textvariable=self.res_var, values=["1080", "2700", "4000"], state="readonly")
        self.res_menu.pack()

        ttk.Button(root, text="Apply Settings", command=self.on_apply).pack(pady=20)

    def on_apply(self):
        fps = int(self.fps_var.get())
        resolution = int(self.res_var.get())

        asyncio.create_task(self.apply_settings(fps, resolution))

    async def scan_bluetooth_devices(self):
        devices = await BleakScanner.discover()
        return [d for d in devices if d.name and "GoPro" in d.name]

    async def apply_settings(self, fps, resolution):
        try:
            matched_devices = await self.scan_bluetooth_devices()

            # Map FPS
            fps_request = {
                60: bytes([0x03, 0x03, 0x01, 0x02]),
                120: bytes([0x03, 0x03, 0x01, 0x01]),
                240: bytes([0x03, 0x03, 0x01, 0x00])
            }[fps]

            # Map Resolution
            resolution_request = {
                1080: bytes([0x03, 0x02, 0x01, 0x09]),
                2700: bytes([0x03, 0x02, 0x01, 0x04]),
                4000: bytes([0x03, 0x02, 0x01, 0x01])
            }[resolution]

            for device in matched_devices:
                identifier = device.name.split(" ")[-1]
                logger.info(f"Processing GoPro: {identifier}")
                event = asyncio.Event()

                async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
                    uuid = GoProUuid(client.services.characteristics[characteristic.handle].uuid)
                    logger.info(f'Received response at {uuid}: {data.hex(":")}')
                    event.set()

                client: BleakClient = await connect_ble(notification_handler, identifier)

                await client.write_gatt_char(GoProUuid.SETTINGS_REQ_UUID.value, fps_request, response=True)
                await event.wait()
                event.clear()

                await client.write_gatt_char(GoProUuid.SETTINGS_REQ_UUID.value, resolution_request, response=True)
                await event.wait()

                await client.disconnect()
                logger.info(f"Disconnected from GoPro {identifier}")

            messagebox.showinfo("Success", "Settings applied to all detected GoPro devices.")

        except Exception as e:
            logger.error(str(e))
            messagebox.showerror("Error", f"Failed to apply settings: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GoProControllerGUI(root)
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))  # Start event loop
    root.mainloop()
