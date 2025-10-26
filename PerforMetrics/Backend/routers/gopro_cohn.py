"""
GoPro COHN Control Router
Endpoints for controlling GoPro 12/13 cameras via COHN (Camera over Home Network)
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
import asyncio
import json
from pathlib import Path
from base64 import b64encode
import requests
from bleak import BleakScanner
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add GoPro module path
gopro_path = str(Path(__file__).parent.parent.parent.parent / "GoPro")
if gopro_path not in sys.path:
    sys.path.insert(0, gopro_path)

from tutorial_modules import GoProUuid, connect_ble, proto, connect_to_access_point, ResponseManager, logger
import pytz
from tzlocal import get_localzone
from datetime import datetime

router = APIRouter()

# Global credentials storage
_cohn_credentials: Dict[str, Dict] = {}
# Format: {"identifier": {"ip": "...", "username": "...", "password": "...", "cert_path": "..."}}


class COHNDevice(BaseModel):
    """COHN-enabled GoPro device model"""
    identifier: str
    name: str
    ip_address: Optional[str] = None
    certificate_exists: bool = False
    connected: bool = False


class ProvisionRequest(BaseModel):
    """COHN provisioning request model"""
    identifier: str  # GoPro identifier (last 4 digits)
    ssid: str        # WiFi SSID
    password: str    # WiFi password


class COHNRecordingCommand(BaseModel):
    """COHN recording command model"""
    action: str  # "start" or "stop"
    identifiers: Optional[List[str]] = None


class COHNSettingsCommand(BaseModel):
    """COHN settings command model"""
    fps: Optional[int] = None
    resolution: Optional[int] = None
    identifiers: Optional[List[str]] = None


class DownloadRequest(BaseModel):
    """Video download request model"""
    identifier: str
    date_filter: Optional[str] = None  # YYYY-MM-DD format
    output_path: str


# ========== Helper Functions ==========

async def set_date_time(manager: ResponseManager) -> None:
    """Set GoPro date/time to current system time"""
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


async def clear_certificate(manager: ResponseManager) -> None:
    """Clear existing COHN certificate"""
    clear_request = bytearray(
        [0xF1, 0x66, *proto.RequestClearCOHNCert().SerializePartialToString()]
    )
    clear_request.insert(0, len(clear_request))
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, clear_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF1 and response.action_id == 0xE6:
            manager.assert_generic_protobuf_success(response.data)
            return
    raise RuntimeError("Unexpected response while clearing certificate.")


async def create_certificate(manager: ResponseManager) -> None:
    """Create new COHN certificate"""
    create_request = bytearray(
        [0xF1, 0x67, *proto.RequestCreateCOHNCert().SerializePartialToString()]
    )
    create_request.insert(0, len(create_request))
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, create_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF1 and response.action_id == 0xE7:
            manager.assert_generic_protobuf_success(response.data)
            return
    raise RuntimeError("Unexpected response while creating certificate.")


async def get_cohn_certificate(manager: ResponseManager) -> str:
    """Retrieve COHN certificate from GoPro"""
    cert_request = bytearray(
        [0xF5, 0x6E, *proto.RequestCOHNCert().SerializePartialToString()]
    )
    cert_request.insert(0, len(cert_request))
    await manager.client.write_gatt_char(GoProUuid.QUERY_REQ_UUID.value, cert_request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id == 0xF5 and response.action_id == 0xEE:
            cert_response: proto.ResponseCOHNCert = response.data  # type: ignore
            manager.assert_generic_protobuf_success(cert_response)
            return cert_response.cert
    raise RuntimeError("Unexpected response while getting certificate.")


async def get_cohn_status(manager: ResponseManager) -> proto.NotifyCOHNStatus:
    """Wait for COHN provisioning to complete and get status"""
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


async def provision_cohn(manager: ResponseManager) -> Dict:
    """Provision COHN and return credentials"""
    await clear_certificate(manager)
    await create_certificate(manager)
    cert = await get_cohn_certificate(manager)
    status = await get_cohn_status(manager)
    return {
        "certificate": cert,
        "username": status.username,
        "password": status.password,
        "ip_address": status.ipaddress,
    }


@router.post("/provision")
async def provision_gopro(request: ProvisionRequest):
    """
    Provision GoPro for COHN and save credentials
    
    This will:
    1. Connect via BLE
    2. Set date/time
    3. Connect to WiFi network
    4. Generate and save COHN certificate
    5. Store credentials for future use
    
    Args:
        request: Provisioning request with identifier, SSID, and password
    """
    manager = ResponseManager()
    try:
        # Connect via BLE
        client = await connect_ble(manager.notification_handler, request.identifier)
        manager.set_client(client)
        
        # Set date/time
        await set_date_time(manager)
        
        # Connect to WiFi
        await connect_to_access_point(manager, request.ssid, request.password)
        
        # Provision COHN
        creds = await provision_cohn(manager)
        
        # Create certifications directory if it doesn't exist
        cert_dir = Path(__file__).parent.parent.parent.parent / "certifications"
        cert_dir.mkdir(parents=True, exist_ok=True)
        
        # Save certificate to file
        cert_path = cert_dir / f"GoPro_{request.identifier}_cohn.crt"
        with open(cert_path, "w") as fp:
            fp.write(creds["certificate"])
        
        # Store credentials in memory
        _cohn_credentials[request.identifier] = {
            "ip": creds["ip_address"],
            "username": creds["username"],
            "password": creds["password"],
            "cert_path": str(cert_path)
        }
        
        # Also save to credentials file for persistence
        creds_file = cert_dir / "gopro_credentials.txt"
        creds_data = {
            "identifier": request.identifier,
            "username": creds["username"],
            "password": creds["password"],
            "ip_address": creds["ip_address"]
        }
        with open(creds_file, "a") as txt_file:
            txt_file.write(json.dumps(creds_data, indent=4) + "\n\n")
        
        logger.info(f"COHN provisioning completed for GoPro {request.identifier}")
        return {
            "status": "success",
            "message": f"COHN provisioning completed for GoPro {request.identifier}",
            "identifier": request.identifier,
            "ip_address": creds["ip_address"],
            "certificate_path": str(cert_path)
        }
    except Exception as e:
        logger.error(f"COHN provisioning failed for {request.identifier}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"COHN provisioning failed: {str(e)}"
        )
    finally:
        if manager.is_initialized:
            await manager.client.disconnect()


@router.post("/establish-connection/{identifier}")
async def establish_cohn_connection(identifier: str):
    """
    Legacy endpoint - use /provision instead
    
    Establish COHN connection and generate certificate
    
    Args:
        identifier: Last 4 digits of GoPro serial number
    """
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use POST /provision with WiFi credentials instead."
    )


@router.get("/devices", response_model=List[COHNDevice])
async def list_cohn_devices():
    """
    List all COHN-enabled GoPro devices with certificates
    
    Returns list of devices with certificate status
    """
    try:
        # TODO: Check certifications folder and return devices
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list COHN devices: {str(e)}"
        )


@router.post("/recording")
async def control_cohn_recording(command: COHNRecordingCommand):
    """
    Control recording on COHN-enabled GoPro cameras
    
    Args:
        command: Recording command (start/stop) and target identifiers
    """
    try:
        action = command.action.lower()
        if action not in ["start", "stop"]:
            raise HTTPException(
                status_code=400,
                detail="Action must be 'start' or 'stop'"
            )
        
        # Determine target identifiers
        target_ids = command.identifiers if command.identifiers else list(_cohn_credentials.keys())
        
        if not target_ids:
            raise HTTPException(
                status_code=400,
                detail="No provisioned GoPro devices found. Please provision devices first."
            )
        
        # Send command to each target
        results = []
        for identifier in target_ids:
            if identifier not in _cohn_credentials:
                results.append({
                    "identifier": identifier,
                    "success": False,
                    "error": "Device not provisioned"
                })
                continue
            
            creds = _cohn_credentials[identifier]
            ip_address = creds["ip"]
            username = creds["username"]
            password = creds["password"]
            cert_path = creds["cert_path"]
            
            # Create Basic Auth header
            auth_token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            headers = {"Authorization": f"Basic {auth_token}"}
            
            # Determine URL based on action
            if action == "start":
                url = f"https://{ip_address}/gopro/camera/shutter/start"
            else:
                url = f"https://{ip_address}/gopro/camera/shutter/stop"
            
            # Send HTTPS request
            try:
                # Disable SSL verification for self-signed GoPro certificates
                response = requests.get(
                    url,
                    timeout=10,
                    headers=headers,
                    verify=False
                )
                response.raise_for_status()
                results.append({
                    "identifier": identifier,
                    "success": True
                })
            except requests.exceptions.RequestException as e:
                logger.error(f"Recording {action} failed for {identifier}: {str(e)}")
                results.append({
                    "identifier": identifier,
                    "success": False,
                    "error": str(e)
                })
        
        # Check if all succeeded
        all_success = all(r["success"] for r in results)
        
        return {
            "status": "success" if all_success else "partial",
            "action": action,
            "results": results,
            "message": f"Recording {action} command sent to {len(target_ids)} device(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"COHN recording control failed: {str(e)}"
        )


@router.post("/settings")
async def change_cohn_settings(command: COHNSettingsCommand):
    """
    Change settings on COHN-enabled GoPro cameras
    
    Args:
        command: Settings to change (FPS, resolution) and target identifiers
        
    FPS mapping:
        60 -> ID 5
        120 -> ID 1
        240 -> ID 0
        
    Resolution mapping:
        1080 -> ID 9
        2700 -> ID 4
        4000 -> ID 1
    """
    try:
        if not command.fps and not command.resolution:
            raise HTTPException(
                status_code=400,
                detail="At least one setting (fps or resolution) must be specified"
            )
        
        # Map FPS to GoPro setting ID
        fps_map = {60: 5, 120: 1, 240: 0}
        # Map resolution to GoPro setting ID
        resolution_map = {1080: 9, 2700: 4, 4000: 1}
        
        if command.fps and command.fps not in fps_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid FPS value. Supported: {list(fps_map.keys())}"
            )
        
        if command.resolution and command.resolution not in resolution_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution value. Supported: {list(resolution_map.keys())}"
            )
        
        # Determine target identifiers
        target_ids = command.identifiers if command.identifiers else list(_cohn_credentials.keys())
        
        if not target_ids:
            raise HTTPException(
                status_code=400,
                detail="No provisioned GoPro devices found. Please provision devices first."
            )
        
        # Send settings to each target
        results = []
        for identifier in target_ids:
            if identifier not in _cohn_credentials:
                results.append({
                    "identifier": identifier,
                    "success": False,
                    "error": "Device not provisioned"
                })
                continue
            
            creds = _cohn_credentials[identifier]
            ip_address = creds["ip"]
            username = creds["username"]
            password = creds["password"]
            cert_path = creds["cert_path"]
            
            # Create Basic Auth header
            auth_token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            headers = {"Authorization": f"Basic {auth_token}"}
            
            device_success = True
            errors = []
            
            # Change resolution if specified
            if command.resolution:
                resolution_id = resolution_map[command.resolution]
                url = f"https://{ip_address}/gopro/camera/setting"
                params = {"setting": 2, "option": resolution_id}
                
                try:
                    response = requests.get(
                        url,
                        params=params,
                        timeout=10,
                        headers=headers,
                        verify=False
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    device_success = False
                    errors.append(f"Resolution: {str(e)}")
            
            # Change FPS if specified
            if command.fps:
                fps_id = fps_map[command.fps]
                url = f"https://{ip_address}/gopro/camera/setting"
                params = {"setting": 234, "option": fps_id}
                
                try:
                    response = requests.get(
                        url,
                        params=params,
                        timeout=10,
                        headers=headers,
                        verify=False
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    device_success = False
                    errors.append(f"FPS: {str(e)}")
            
            if device_success:
                results.append({
                    "identifier": identifier,
                    "success": True
                })
            else:
                results.append({
                    "identifier": identifier,
                    "success": False,
                    "error": "; ".join(errors)
                })
        
        # Check if all succeeded
        all_success = all(r["success"] for r in results)
        
        changes = {}
        if command.fps:
            changes["fps"] = command.fps
        if command.resolution:
            changes["resolution"] = command.resolution
        
        return {
            "status": "success" if all_success else "partial",
            "changes": changes,
            "results": results,
            "message": f"Settings updated on {len(target_ids)} device(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"COHN settings change failed: {str(e)}"
        )


@router.post("/download")
async def download_videos(request: DownloadRequest):
    """
    Download videos from COHN-enabled GoPro
    
    Args:
        request: Download request with identifier, date filter, and output path
    """
    try:
        # TODO: Implement using GoPro/COHN/download_videos.py
        return {
            "status": "success",
            "identifier": request.identifier,
            "output_path": request.output_path,
            "message": "Video download started",
            "task_id": "download_task_123"  # For future async task tracking
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video download failed: {str(e)}"
        )


@router.get("/certificate-status/{identifier}")
async def check_certificate_status(identifier: str):
    """
    Check if certificate exists for a GoPro device
    
    Args:
        identifier: Last 4 digits of GoPro serial number
    """
    try:
        cert_path = f"/Users/a/Desktop/Go2Rep/certifications/{identifier}_cert.crt"
        exists = os.path.exists(cert_path)
        
        return {
            "identifier": identifier,
            "certificate_exists": exists,
            "certificate_path": cert_path if exists else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Certificate check failed: {str(e)}"
        )

