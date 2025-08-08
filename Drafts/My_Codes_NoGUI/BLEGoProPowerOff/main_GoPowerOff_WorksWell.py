import argparse
import asyncio
from rich.console import Console
import nest_asyncio # Import nest_asyncio

from open_gopro import WiredGoPro, WirelessGoPro
from open_gopro.logger import setup_logging
from open_gopro.util import add_cli_args_and_parse

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

console = Console()

async def power_off_camera(args: argparse.Namespace) -> None:
    """
    Connects to a GoPro camera and sends a power off command.
    """
    logger = setup_logging(__name__, args.log)
    gopro: WirelessGoPro | WiredGoPro | None = None

    try:
        async with (
            WiredGoPro(args.identifier)
            if args.wired
            else WirelessGoPro(args.identifier, wifi_interface=args.wifi_interface)
        ) as gopro:
            assert gopro
            console.print("Sending power off command...")
            response = await gopro.ble_command.power_down()
            if response.ok:
                console.print("[green]Camera powered down successfully.[/green]")
            else:
                console.print(f"[red]Failed to power down camera: {response.error_message}[/red]")
    except Exception as e:
        logger.error(f"An error occurred: {repr(e)}")
        console.print(f"[red]An error occurred: {e}[/red]")
    finally:
        if gopro:
            console.print("Closing GoPro connection...")
            await gopro.close()
        console.print("Exiting power off process.")

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for camera connection.
    """
    parser = argparse.ArgumentParser(description="Turn off a GoPro camera.")
    parser.add_argument("--wired", action="store_true", help="Use wired (USB) connection.")
    # Add other necessary arguments from add_cli_args_and_parse if not already handled
    # For example:
    # parser.add_argument("--identifier", type=str, help="Camera identifier (name or MAC address).", required=True)
    # parser.add_argument("--wifi-interface", type=str, help="Specify Wi-Fi interface (e.g., wlan0).")
    # parser.add_argument("--log", action="store_true", help="Enable logging.")
    
    # Using the utility function to add common CLI args
    return add_cli_args_and_parse(parser)

def entrypoint() -> None:
    """
    Main entry point of the script.
    """
    args = parse_arguments()
    asyncio.run(power_off_camera(args))

if __name__ == "__main__":
    entrypoint()