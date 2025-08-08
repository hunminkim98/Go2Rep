import argparse
import asyncio
from rich.console import Console
import nest_asyncio
from bleak import BleakScanner, BLEDevice

from open_gopro import WirelessGoPro, WiredGoPro
from open_gopro.logger import setup_logging

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

console = Console()

async def power_off_all_gopros(args: argparse.Namespace) -> None:
    """
    Scans for all GoPro cameras and sends a power off command to each.
    """
    logger = setup_logging(__name__, args.log)
    
    console.print("Scanning for GoPro devices...")
    matched_devices = []
    try:
        # Perform a single, comprehensive scan
        devices = await BleakScanner.discover()
    except Exception as e:
        console.print(f"[red]Error during Bluetooth scan: {e}[/red]")
        logger.error(f"Error during Bluetooth scan: {repr(e)}")
        return
        
    if not devices:
        console.print("[yellow]No Bluetooth devices found.[/yellow]")
    else:
        for device in devices:
            if device.name and "GoPro" in device.name:
                matched_devices.append(device)
                
    if not matched_devices:
        console.print("[red]No GoPro cameras found to power off.[/red]")
        return

    console.print(f"Found {len(matched_devices)} GoPro cameras. Attempting to power them off...")
    
    tasks = []
    for device in matched_devices:
        # Pass the entire BLEDevice object to the power_off_single_camera function
        tasks.append(power_off_single_camera(device, args.wired, args.wifi_interface, logger))
    
    await asyncio.gather(*tasks)
    console.print("[green]Attempted to power off all found GoPro cameras.[/green]")

# Modified to accept BLEDevice directly
async def power_off_single_camera(device: BLEDevice, wired: bool, wifi_interface: str | None, logger) -> None:
    """
    Connects to a single GoPro camera (using its discovered BLEDevice object)
    and sends a power off command.
    """
    gopro: WirelessGoPro | WiredGoPro | None = None
    identifier = device.name.split(" ")[-1] if device.name and "GoPro" in device.name else device.address # For logging / display
    
    try:
        console.print(f"Connecting to GoPro: {identifier} (address: {device.address})...")
        async with (
            WiredGoPro(identifier) # WiredGoPro still uses identifier / address
            if wired
            else WirelessGoPro(device, wifi_interface=wifi_interface) # Pass device object here
        ) as gopro:
            assert gopro
            console.print(f"Sending power off command to GoPro: {identifier}...")
            response = await gopro.ble_command.power_down()
            if response.ok:
                console.print(f"[green]GoPro {identifier} powered down successfully.[/green]")
            else:
                console.print(f"[red]Failed to power down GoPro {identifier}: {response.error_message}[/red]")
    except Exception as e:
        logger.error(f"An error occurred with GoPro {identifier}: {repr(e)}")
        console.print(f"[red]An error occurred with GoPro {identifier}: {e}[/red]")
    finally:
        if gopro:
            console.print(f"Closing connection to GoPro {identifier}...")
            # The 'async with' block handles closing automatically. No need for explicit gopro.close() here.
            pass 

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for turning off all GoPro cameras.
    """
    parser = argparse.ArgumentParser(description="Turn off all accessible GoPro cameras.")
    
    # Manually add the arguments we need
    parser.add_argument("--wired", action="store_true", help="Use wired (USB) connection for all cameras (less common for multiple).")
    parser.add_argument("--wifi-interface", type=str, help="Specify Wi-Fi interface (e.g., wlan0).")
    parser.add_argument("--log", action="store_true", help="Enable logging.")
    
    return parser.parse_args()


def entrypoint() -> None:
    """
    Main entry point of the script.
    """
    args = parse_arguments()
    asyncio.run(power_off_all_gopros(args))

if __name__ == "__main__":
    entrypoint()