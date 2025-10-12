"""
Download adapters for GoPro video collection

Provides adapter interface and implementations for both legacy and GP13 collectors.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Callable, Optional, Protocol
from datetime import datetime
import os


class DownloadAdapter(Protocol):
    """Protocol for GoPro video download adapters"""
    
    async def list_files(self, camera_id: str) -> List[Dict]:
        """List available files on the camera"""
        ...
        
    async def download(self, camera_id: str, file: Dict, dest: Path, 
                      progress_cb: Optional[Callable[[int], None]] = None) -> Path:
        """Download a file from camera to destination"""
        ...
        
    def cancel(self, camera_id: str):
        """Cancel ongoing downloads for a camera"""
        ...


class MockDownloadAdapter:
    """Mock adapter for testing"""
    
    def __init__(self):
        self._mock_files = {
            "gopro_001": [
                {"name": "GH010001.MP4", "size": 15728640, "date": "2024-01-15 10:30:00"},
                {"name": "GH010002.MP4", "size": 20971520, "date": "2024-01-15 10:35:00"},
                {"name": "GH010003.MP4", "size": 12582912, "date": "2024-01-15 10:40:00"},
            ],
            "gopro_002": [
                {"name": "GH020001.MP4", "size": 18874368, "date": "2024-01-15 10:32:00"},
                {"name": "GH020002.MP4", "size": 16777216, "date": "2024-01-15 10:37:00"},
            ],
            "gopro_003": [
                {"name": "GH030001.MP4", "size": 14680064, "date": "2024-01-15 10:33:00"},
                {"name": "GH030002.MP4", "size": 22020096, "date": "2024-01-15 10:38:00"},
                {"name": "GH030003.MP4", "size": 10485760, "date": "2024-01-15 10:43:00"},
            ]
        }
        self._cancelled = set()
    
    async def list_files(self, camera_id: str) -> List[Dict]:
        """List mock files"""
        await asyncio.sleep(0.5)  # Simulate network delay
        return self._mock_files.get(camera_id, [])
    
    async def download(self, camera_id: str, file: Dict, dest: Path, 
                      progress_cb: Optional[Callable[[int], None]] = None) -> Path:
        """Simulate file download"""
        if camera_id in self._cancelled:
            raise asyncio.CancelledError("Download cancelled")
            
        # Create destination directory
        dest.mkdir(parents=True, exist_ok=True)
        
        # Simulate download with progress
        file_size = file["size"]
        downloaded = 0
        chunk_size = file_size // 20  # 20 progress updates
        
        for i in range(20):
            if camera_id in self._cancelled:
                raise asyncio.CancelledError("Download cancelled")
                
            await asyncio.sleep(0.1)  # Simulate download time
            downloaded += chunk_size
            
            if progress_cb:
                progress_cb(int((downloaded / file_size) * 100))
        
        # Create mock file
        mock_file = dest / file["name"]
        mock_file.write_bytes(b"Mock video content")
        
        return mock_file
    
    def cancel(self, camera_id: str):
        """Cancel downloads for camera"""
        self._cancelled.add(camera_id)


class LegacyCollectorAdapter:
    """Adapter for legacy gopro_video_collector.py"""
    
    def __init__(self):
        self._collector = None
        self._cancelled = set()
    
    async def list_files(self, camera_id: str) -> List[Dict]:
        """List files using legacy collector"""
        # Import here to avoid circular imports
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent.parent / "tools"))
        
        try:
            from gopro_video_collector import GoProVideoCollector
            
            # Initialize collector if needed
            if self._collector is None:
                self._collector = GoProVideoCollector()
            
            # Run in thread pool to avoid blocking
            files = await asyncio.to_thread(self._collector.list_files, camera_id)
            
            # Convert to standard format
            result = []
            for file_info in files:
                result.append({
                    "name": file_info.get("filename", ""),
                    "size": file_info.get("size", 0),
                    "date": file_info.get("date", ""),
                    "path": file_info.get("path", "")
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Legacy collector error: {str(e)}")
    
    async def download(self, camera_id: str, file: Dict, dest: Path, 
                      progress_cb: Optional[Callable[[int], None]] = None) -> Path:
        """Download file using legacy collector"""
        if camera_id in self._cancelled:
            raise asyncio.CancelledError("Download cancelled")
            
        # Create destination directory
        dest.mkdir(parents=True, exist_ok=True)
        
        try:
            # Run download in thread pool
            result_path = await asyncio.to_thread(
                self._collector.download_file,
                camera_id,
                file["path"],
                str(dest),
                progress_cb
            )
            
            return Path(result_path)
            
        except Exception as e:
            raise Exception(f"Legacy download error: {str(e)}")
    
    def cancel(self, camera_id: str):
        """Cancel downloads for camera"""
        self._cancelled.add(camera_id)
        if self._collector:
            # Cancel any ongoing operations
            pass


class GP13CollectorAdapter:
    """Adapter for GP13 gopro_video_collector_GP13.py"""
    
    def __init__(self):
        self._collector = None
        self._cancelled = set()
    
    async def list_files(self, camera_id: str) -> List[Dict]:
        """List files using GP13 collector"""
        # Import here to avoid circular imports
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent.parent / "tools"))
        
        try:
            from gopro_video_collector_GP13 import GoProVideoCollectorGP13
            
            # Initialize collector if needed
            if self._collector is None:
                self._collector = GoProVideoCollectorGP13()
            
            # Run in thread pool to avoid blocking
            files = await asyncio.to_thread(self._collector.list_files, camera_id)
            
            # Convert to standard format
            result = []
            for file_info in files:
                result.append({
                    "name": file_info.get("filename", ""),
                    "size": file_info.get("size", 0),
                    "date": file_info.get("date", ""),
                    "path": file_info.get("path", "")
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"GP13 collector error: {str(e)}")
    
    async def download(self, camera_id: str, file: Dict, dest: Path, 
                      progress_cb: Optional[Callable[[int], None]] = None) -> Path:
        """Download file using GP13 collector"""
        if camera_id in self._cancelled:
            raise asyncio.CancelledError("Download cancelled")
            
        # Create destination directory
        dest.mkdir(parents=True, exist_ok=True)
        
        try:
            # Run download in thread pool
            result_path = await asyncio.to_thread(
                self._collector.download_file,
                camera_id,
                file["path"],
                str(dest),
                progress_cb
            )
            
            return Path(result_path)
            
        except Exception as e:
            raise Exception(f"GP13 download error: {str(e)}")
    
    def cancel(self, camera_id: str):
        """Cancel downloads for camera"""
        self._cancelled.add(camera_id)
        if self._collector:
            # Cancel any ongoing operations
            pass


def create_download_adapter(adapter_type: str) -> DownloadAdapter:
    """Factory function to create download adapter"""
    if adapter_type == "mock":
        return MockDownloadAdapter()
    elif adapter_type == "legacy":
        return LegacyCollectorAdapter()
    elif adapter_type == "gp13":
        return GP13CollectorAdapter()
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")


def get_download_path(camera_id: str) -> Path:
    """Get standard download path for camera"""
    from os.path import expanduser
    base = Path(expanduser('~')) / 'PerforMetrics' / 'Downloads' / camera_id / datetime.now().strftime('%Y-%m-%d')
    base.mkdir(parents=True, exist_ok=True)
    return base
