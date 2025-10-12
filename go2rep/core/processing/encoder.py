"""
Video encoder for Go2Rep v2.0

This module provides video encoding capabilities with support for
multiple backends (FFmpeg and PyAV) for flexibility and performance.
"""

import subprocess
import os
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import shutil


class EncoderBackend(Enum):
    """Available encoder backends"""
    FFMPEG = "ffmpeg"
    PYAV = "pyav"


class VideoEncoder:
    """
    Video encoder with support for multiple backends
    
    Supports both FFmpeg (CLI) and PyAV (Python library) backends
    for video transcoding operations.
    """
    
    def __init__(self, backend: EncoderBackend = EncoderBackend.FFMPEG):
        """
        Initialize video encoder
        
        Args:
            backend: Encoder backend to use
        """
        self.backend = backend
        self._validate_backend()
    
    def _validate_backend(self):
        """Validate that the selected backend is available"""
        if self.backend == EncoderBackend.FFMPEG:
            if not self._check_ffmpeg():
                raise RuntimeError("FFmpeg not found. Please install FFmpeg or use PyAV backend.")
        elif self.backend == EncoderBackend.PYAV:
            if not self._check_pyav():
                raise RuntimeError("PyAV not available. Please install PyAV or use FFmpeg backend.")
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_pyav(self) -> bool:
        """Check if PyAV is available"""
        try:
            import av
            return True
        except ImportError:
            return False
    
    def transcode(self, 
                  src: str, 
                  dst: str, 
                  *,
                  fps: Optional[int] = None,
                  crf: int = 18,
                  preset: str = "medium",
                  dry_run: bool = False) -> None:
        """
        Transcode video file
        
        Args:
            src: Source video file path
            dst: Destination video file path
            fps: Target frame rate (None = keep original)
            crf: Constant Rate Factor (0-51, lower = better quality)
            preset: Encoding preset (ultrafast, fast, medium, slow, etc.)
            dry_run: If True, only validate parameters without encoding
        """
        src_path = Path(src)
        dst_path = Path(dst)
        
        # Validate inputs
        if not src_path.exists():
            raise ValueError(f"Source file not found: {src}")
        
        if dst_path.exists():
            raise ValueError(f"Destination file already exists: {dst}")
        
        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dry_run:
            print(f"Dry run: Would transcode {src} -> {dst}")
            print(f"Parameters: fps={fps}, crf={crf}, preset={preset}")
            return
        
        # Perform transcoding based on backend
        if self.backend == EncoderBackend.FFMPEG:
            self._transcode_ffmpeg(src, dst, fps=fps, crf=crf, preset=preset)
        elif self.backend == EncoderBackend.PYAV:
            self._transcode_pyav(src, dst, fps=fps, crf=crf, preset=preset)
    
    def _transcode_ffmpeg(self, 
                         src: str, 
                         dst: str, 
                         fps: Optional[int] = None,
                         crf: int = 18,
                         preset: str = "medium") -> None:
        """Transcode using FFmpeg CLI"""
        cmd = [
            "ffmpeg",
            "-i", src,
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", "128k"
        ]
        
        if fps is not None:
            cmd.extend(["-r", str(fps)])
        
        cmd.append(dst)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg encoding timed out")
        except Exception as e:
            raise RuntimeError(f"FFmpeg encoding failed: {e}")
    
    def _transcode_pyav(self, 
                       src: str, 
                       dst: str, 
                       fps: Optional[int] = None,
                       crf: int = 18,
                       preset: str = "medium") -> None:
        """Transcode using PyAV library"""
        try:
            import av
        except ImportError:
            raise RuntimeError("PyAV not available")
        
        try:
            # Open input container
            input_container = av.open(src)
            input_video_stream = input_container.streams.video[0]
            
            # Open output container
            output_container = av.open(dst, mode='w')
            
            # Add video stream to output
            output_video_stream = output_container.add_stream('libx264')
            output_video_stream.width = input_video_stream.width
            output_video_stream.height = input_video_stream.height
            
            # Set frame rate
            if fps is not None:
                output_video_stream.rate = fps
            else:
                output_video_stream.rate = input_video_stream.rate
            
            # Set encoding options
            output_video_stream.options = {
                'crf': str(crf),
                'preset': preset
            }
            
            # Add audio stream if present
            if len(input_container.streams.audio) > 0:
                output_audio_stream = output_container.add_stream('aac')
                output_audio_stream.rate = 44100
                output_audio_stream.channels = 2
            
            # Transcode frames
            for frame in input_container.decode(input_video_stream):
                frame.pts = None  # Let PyAV handle timestamps
                output_container.mux(output_video_stream.encode(frame))
            
            # Transcode audio if present
            if len(input_container.streams.audio) > 0:
                input_audio_stream = input_container.streams.audio[0]
                for frame in input_container.decode(input_audio_stream):
                    frame.pts = None
                    output_container.mux(output_audio_stream.encode(frame))
            
            # Close containers
            input_container.close()
            output_container.close()
            
        except Exception as e:
            raise RuntimeError(f"PyAV encoding failed: {e}")
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        if self.backend == EncoderBackend.FFMPEG:
            return self._get_video_info_ffmpeg(video_path)
        elif self.backend == EncoderBackend.PYAV:
            return self._get_video_info_pyav(video_path)
    
    def _get_video_info_ffmpeg(self, video_path: str) -> Dict[str, Any]:
        """Get video info using FFmpeg"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe failed: {result.stderr}")
            
            import json
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                raise RuntimeError("No video stream found")
            
            return {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "size": int(data.get("format", {}).get("size", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                "codec": video_stream.get("codec_name", "unknown"),
                "bitrate": int(video_stream.get("bit_rate", 0))
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFprobe timed out")
        except Exception as e:
            raise RuntimeError(f"FFprobe failed: {e}")
    
    def _get_video_info_pyav(self, video_path: str) -> Dict[str, Any]:
        """Get video info using PyAV"""
        try:
            import av
        except ImportError:
            raise RuntimeError("PyAV not available")
        
        try:
            container = av.open(video_path)
            video_stream = container.streams.video[0]
            
            info = {
                "duration": float(container.duration) / av.time_base if container.duration else 0,
                "size": Path(video_path).stat().st_size,
                "width": video_stream.width,
                "height": video_stream.height,
                "fps": float(video_stream.rate),
                "codec": video_stream.codec.name,
                "bitrate": video_stream.bit_rate or 0
            }
            
            container.close()
            return info
            
        except Exception as e:
            raise RuntimeError(f"PyAV info extraction failed: {e}")
    
    def validate_video(self, video_path: str) -> bool:
        """
        Validate video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if video is valid
        """
        try:
            info = self.get_video_info(video_path)
            return info["width"] > 0 and info["height"] > 0 and info["fps"] > 0
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats
        
        Returns:
            List of supported format extensions
        """
        if self.backend == EncoderBackend.FFMPEG:
            return [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        elif self.backend == EncoderBackend.PYAV:
            return [".mp4", ".avi", ".mov", ".mkv"]
        
        return []
    
    def estimate_output_size(self, 
                           src: str, 
                           crf: int = 18) -> int:
        """
        Estimate output file size
        
        Args:
            src: Source video file path
            crf: Constant Rate Factor
            
        Returns:
            Estimated output size in bytes
        """
        try:
            info = self.get_video_info(src)
            duration = info["duration"]
            width = info["width"]
            height = info["height"]
            
            # Rough estimation based on resolution and CRF
            pixels_per_second = width * height * info["fps"]
            
            # CRF-based bitrate estimation (very rough)
            if crf <= 18:
                bits_per_pixel = 0.1
            elif crf <= 23:
                bits_per_pixel = 0.05
            elif crf <= 28:
                bits_per_pixel = 0.02
            else:
                bits_per_pixel = 0.01
            
            estimated_bits = pixels_per_second * duration * bits_per_pixel
            estimated_bytes = int(estimated_bits / 8)
            
            return estimated_bytes
            
        except Exception:
            # Fallback: assume 50% of original size
            return Path(src).stat().st_size // 2
