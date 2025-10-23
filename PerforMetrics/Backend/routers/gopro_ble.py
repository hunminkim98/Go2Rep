"""
GoPro BLE Control Router
Endpoints for controlling GoPro cameras via Bluetooth Low Energy
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from bleak import BleakScanner

router = APIRouter()


class GoProDevice(BaseModel):
    """GoPro device model"""
    identifier: str
    name: str
    address: str
    connected: bool = False


class RecordingCommand(BaseModel):
    """Recording command model"""
    action: str  # "start" or "stop"
    identifiers: Optional[List[str]] = None  # If None, apply to all


class SettingsCommand(BaseModel):
    """Settings command model"""
    fps: Optional[int] = None  # 60, 120, 240
    resolution: Optional[int] = None  # 1080, 2700, 4000
    identifiers: Optional[List[str]] = None


@router.get("/scan", response_model=List[GoProDevice])
async def scan_gopros():
    """
    Scan for available GoPro cameras via BLE
    
    Returns list of discovered GoPro devices
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting BLE scan...")
        matched_devices = []
        
        # Scan with longer timeout for better detection
        devices = await BleakScanner.discover(timeout=10.0)
        logger.info(f"BLE scan completed. Found {len(devices)} total devices.")
        
        if not devices:
            logger.warning("No Bluetooth devices found at all. Check Bluetooth permissions and hardware.")
            return []
        
        # Log all discovered devices for debugging
        for device in devices:
            logger.debug(f"Found device: {device.name} ({device.address})")
            if device.name and "GoPro" in device.name:
                # Extract identifier (last 4 digits) from device name
                # e.g., "GoPro 1234" -> "1234"
                identifier = device.name.split(" ")[-1] if " " in device.name else device.name
                
                logger.info(f"Matched GoPro: {device.name} (identifier: {identifier})")
                matched_devices.append(GoProDevice(
                    identifier=identifier,
                    name=device.name,
                    address=device.address,
                    connected=False
                ))
        
        logger.info(f"Scan completed. Found {len(matched_devices)} GoPro device(s).")
        return matched_devices
        
    except PermissionError as e:
        logger.error(f"Permission error during BLE scan: {str(e)}")
        raise HTTPException(
            status_code=403, 
            detail=f"Bluetooth permission denied. Please grant Bluetooth access to the application. Error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"BLE scan failed with error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"BLE scan failed: {str(e)}")


@router.post("/connect/{identifier}")
async def connect_gopro(identifier: str):
    """
    Connect to a specific GoPro camera
    
    Args:
        identifier: Last 4 digits of GoPro serial number
    """
    try:
        # TODO: Implement BLE connection logic
        return {
            "status": "success",
            "message": f"Connected to GoPro {identifier}",
            "identifier": identifier
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to GoPro {identifier}: {str(e)}"
        )


@router.post("/recording")
async def control_recording(command: RecordingCommand):
    """
    Control recording on GoPro cameras
    
    Args:
        command: Recording command (start/stop) and target identifiers
    """
    try:
        # TODO: Implement recording control using GoPro/BLE/start_recording.py
        action = command.action.lower()
        if action not in ["start", "stop"]:
            raise HTTPException(
                status_code=400,
                detail="Action must be 'start' or 'stop'"
            )
        
        targets = command.identifiers if command.identifiers else ["all"]
        
        return {
            "status": "success",
            "action": action,
            "targets": targets,
            "message": f"Recording {action} command sent"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recording control failed: {str(e)}"
        )


@router.post("/settings")
async def change_settings(command: SettingsCommand):
    """
    Change GoPro camera settings
    
    Args:
        command: Settings to change (FPS, resolution) and target identifiers
    """
    try:
        # TODO: Implement settings change using GoPro/BLE/change_settings.py
        changes = {}
        if command.fps:
            if command.fps not in [60, 120, 240]:
                raise HTTPException(
                    status_code=400,
                    detail="FPS must be 60, 120, or 240"
                )
            changes["fps"] = command.fps
            
        if command.resolution:
            if command.resolution not in [1080, 2700, 4000]:
                raise HTTPException(
                    status_code=400,
                    detail="Resolution must be 1080, 2700, or 4000"
                )
            changes["resolution"] = command.resolution
        
        targets = command.identifiers if command.identifiers else ["all"]
        
        return {
            "status": "success",
            "changes": changes,
            "targets": targets,
            "message": "Settings updated"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Settings change failed: {str(e)}"
        )


@router.post("/power-off/{identifier}")
async def power_off_gopro(identifier: str):
    """
    Power off a specific GoPro camera
    
    Args:
        identifier: Last 4 digits of GoPro serial number
    """
    try:
        # TODO: Implement power off using GoPro/BLE/power_off.py
        return {
            "status": "success",
            "message": f"Power off command sent to GoPro {identifier}",
            "identifier": identifier
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Power off failed: {str(e)}"
        )


@router.get("/health/{identifier}")
async def check_device_health(identifier: str):
    """
    Check if a specific GoPro device is still connected and responsive
    
    Args:
        identifier: Last 4 digits of GoPro serial number
        
    Returns:
        200 if device is connected and responsive
        503 if device is not connected or not responsive
    """
    try:
        # TODO: Implement actual health check by querying device status
        # In real implementation, this would:
        # 1. Check if device is in connected devices list
        # 2. Try to query device status/battery level
        # 3. Return 200 if responsive, 503 if not
        
        raise HTTPException(
            status_code=503,
            detail=f"GoPro {identifier} health check not implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed for GoPro {identifier}: {str(e)}"
        )


@router.post("/reconnect/{identifier}")
async def reconnect_gopro(identifier: str):
    """
    Attempt to reconnect to a specific GoPro camera
    
    Args:
        identifier: Last 4 digits of GoPro serial number
    """
    try:
        # TODO: Implement actual reconnection logic
        # This should:
        # 1. Check if device is already connected
        # 2. If not, attempt BLE reconnection
        # 3. Restore previous settings if needed
        
        raise HTTPException(
            status_code=503,
            detail=f"GoPro {identifier} reconnection not implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Reconnection failed for GoPro {identifier}: {str(e)}"
        )

