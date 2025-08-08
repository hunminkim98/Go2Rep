import sys
import json
import asyncio
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import pytz
from tzlocal import get_localzone
import nest_asyncio
import platform
import shutil
nest_asyncio.apply()

from tutorial_modules import GoProUuid, connect_ble, proto, connect_to_access_point, ResponseManager, logger
from bleak import BleakScanner


# ========== Helper Data Classes ==========

@dataclass(frozen=True)
class Credentials:
    certificate: str
    username: str
    password: str
    ip_address: str

    def __str__(self) -> str:
        return json.dumps(asdict(self), indent=4)


# ========== BLE Device Scanner ==========

async def scan_bluetooth_devices():
    matched_devices = []
    devices = await BleakScanner.discover()
    if not devices:
        print("No Bluetooth devices found.")
    else:
        print(f"Found {len(devices)} devices:")
        for device in devices:
            if device.name and "GoPro" in device.name:
                matched_devices.append(device)
    return matched_devices


# ========== Provisioning Steps ==========

async def set_date_time(manager: ResponseManager) -> None:
    tz = pytz.timezone(get_localzone().key)
    now = tz.localize(datetime.now(), is_dst=None)
    try:
        is_dst = now.tzinfo._dst.seconds != 0  # type: ignore
        offset = (now.utcoffset().total_seconds() - now.tzinfo._dst.seconds) / 60  # type: ignore
    except AttributeError:
        is_dst = False
        offset = (now.utcoffset().total_seconds()) / 60  # type: ignore
    if is_dst:
        offset += 60
    offset = int(offset)
    logger.info(f"Setting date/time to {now}:{offset} {is_dst=}")

    datetime_request = bytearray(
        [
            0x0F,
            10,
            *now.year.to_bytes(2, "big"),
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
            *offset.to_bytes(2, "big", signed=True),
            is_dst,
        ]
    )
    datetime_request.insert(0, len(datetime_request))
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, datetime_request, response=True)
    response = await manager.get_next_response_as_tlv()
    assert response.id == 0x0F and response.status == 0x00
    logger.info("Date/time set successfully.")


async def clear_certificate(manager: ResponseManager) -> None:
    logger.info("Clearing COHN certificate.")
    clear_request = bytearray(
        [0xF1, 0x66, *proto.RequestClearCOHNCert().SerializePartialToString()]
    )
    clear_request.insert(0, len(clear_request))
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, clear_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF1 and response.action_id == 0xE6:
            manager.assert_generic_protobuf_success(response.data)
            logger.info("COHN certificate cleared.")
            return
    raise RuntimeError("Unexpected response while clearing certificate.")


async def create_certificate(manager: ResponseManager) -> None:
    logger.info("Creating new COHN certificate.")
    create_request = bytearray(
        [0xF1, 0x67, *proto.RequestCreateCOHNCert().SerializePartialToString()]
    )
    create_request.insert(0, len(create_request))
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, create_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF1 and response.action_id == 0xE7:
            manager.assert_generic_protobuf_success(response.data)
            logger.info("COHN certificate created.")
            return
    raise RuntimeError("Unexpected response while creating certificate.")


async def get_cohn_certificate(manager: ResponseManager) -> str:
    logger.info("Retrieving COHN certificate.")
    cert_request = bytearray(
        [0xF5, 0x6E, *proto.RequestCOHNCert().SerializePartialToString()]
    )
    cert_request.insert(0, len(cert_request))
    await manager.client.write_gatt_char(GoProUuid.QUERY_REQ_UUID.value, cert_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF5 and response.action_id == 0xEE:
            cert_response: proto.ResponseCOHNCert = response.data  # type: ignore
            manager.assert_generic_protobuf_success(cert_response)
            logger.info("Certificate received.")
            return cert_response.cert
    raise RuntimeError("Unexpected response while getting certificate.")


async def get_cohn_status(manager: ResponseManager) -> proto.NotifyCOHNStatus:
    logger.info("Waiting for COHN provisioning...")
    status_request = bytearray(
        [0xF5, 0x6F, *proto.RequestGetCOHNStatus(register_cohn_status=True).SerializePartialToString()]
    )
    status_request.insert(0, len(status_request))
    await manager.client.write_gatt_char(GoProUuid.QUERY_REQ_UUID.value, status_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF5 and response.action_id == 0xEF:
            cohn_status: proto.NotifyCOHNStatus = response.data  # type: ignore
            if cohn_status.state == proto.EnumCOHNNetworkState.COHN_STATE_NetworkConnected:
                return cohn_status
    raise RuntimeError("COHN not connected after request.")


async def provision_cohn(manager: ResponseManager) -> Credentials:
    await clear_certificate(manager)
    await create_certificate(manager)
    cert = await get_cohn_certificate(manager)
    status = await get_cohn_status(manager)
    logger.info("Provisioned COHN.")
    return Credentials(
        certificate=cert,
        username=status.username,
        password=status.password,
        ip_address=status.ipaddress,
    )


# ========== Main Provisioning Per Camera ==========

async def provision_one_gopro(ssid: str, password: str, identifier: str, cert_path: Path) -> Credentials | None:
    manager = ResponseManager()
    try:
        client = await connect_ble(manager.notification_handler, identifier)
        manager.set_client(client)
        await set_date_time(manager)
        await connect_to_access_point(manager, ssid, password)
        creds = await provision_cohn(manager)

        # Save certificate to file
        with open(cert_path, "w") as fp:
            fp.write(creds.certificate)
        logger.info(f"Saved certificate to {cert_path}")

        # Save credentials (excluding certificate) to shared text file
        credentials_txt = cert_path.parent / "gopro_credentials.txt"
        creds_data = {
            "identifier": identifier,
            "username": creds.username,
            "password": creds.password,
            "ip_address": creds.ip_address
        }
        with open(credentials_txt, "a") as txt_file:
            txt_file.write(json.dumps(creds_data, indent=4) + "\n\n")
        logger.info(f"Saved credentials to {credentials_txt}")

        return creds
    except Exception as exc:
        logger.error(f"[{identifier}] Error: {exc}")
        return None
    finally:
        if manager.is_initialized:
            await manager.client.disconnect()
            


# ========== Batch Provisioning ==========

async def provision_all_gopros(ssid: str, password: str, certificate_dir: Path):
    matched_devices = await scan_bluetooth_devices()

    if not matched_devices:
        logger.warning("No GoPro cameras found.")
        return

    logger.info(f"Provisioning {len(matched_devices)} GoPro cameras...")
    
    # 🔁 Delete gopro_credentials.txt before starting
    credentials_txt = certificate_dir / "gopro_credentials.txt"
    if credentials_txt.exists():
        credentials_txt.unlink()
        logger.info(f"Deleted existing {credentials_txt}")
        
    for device in matched_devices:
        identifier = device.name.split(" ")[-1]
        cert_file = certificate_dir / f"GoPro_{identifier}_cohn.crt"
        await provision_one_gopro(ssid, password, identifier, cert_file)

    logger.info("Provisioning complete.")

def scan_wifi_networks() -> list[str]:
    """Scans and returns a list of available Wi-Fi SSIDs."""
    ssids = set()
    system = platform.system()

    try:
        if system == "Windows":
            output = subprocess.check_output(["netsh", "wlan", "show", "networks"], encoding="utf-8")
            for line in output.splitlines():
                if "SSID" in line and ":" in line:
                    ssid = line.split(":", 1)[1].strip()
                    if ssid:
                        ssids.add(ssid)

        elif system == "Darwin":  # macOS
            output = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"], encoding="utf-8")
            for line in output.splitlines()[1:]:
                ssid = line.strip().split()[0]
                if ssid:
                    ssids.add(ssid)

        elif system == "Linux":
            output = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], encoding="utf-8")
            for line in output.strip().splitlines():
                ssid = line.strip()
                if ssid:
                    ssids.add(ssid)

    except subprocess.CalledProcessError as e:
        logger.error(f"Wi-Fi scan failed: {e}")

    return sorted(ssids)

# ========== CLI Entrypoint ==========

async def main():
    # Scan for available Wi-Fi networks
    wifi_list = scan_wifi_networks()
    if not wifi_list:
        print("⚠️ No Wi-Fi networks found.")
        return

    print("Available Wi-Fi networks:")
    for idx, ssid in enumerate(wifi_list):
        print(f"{idx + 1}. {ssid}")

    # Ask user to choose
    while True:
        try:
            choice = int(input("Select Wi-Fi network number: ")) - 1
            if 0 <= choice < len(wifi_list):
                ssid = wifi_list[choice]
                break
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    password = input(f"Enter password for '{ssid}': ").strip()
    cert_dir = Path("./certifications")
    if cert_dir.exists() and cert_dir.is_dir():
        shutil.rmtree(cert_dir)  # Delete the directory if it exists
    cert_dir.mkdir(parents=True, exist_ok=True)  # Recreate it
    await provision_all_gopros(ssid, password, cert_dir)

# Ensure compatibility with Spyder (IPython)
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())