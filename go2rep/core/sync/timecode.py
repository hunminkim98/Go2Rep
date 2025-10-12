"""
Timecode-based video synchronization engine for Go2Rep v2.0

This module wraps the existing timecode_synchronizer.py functionality
to provide automatic synchronization based on video metadata.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# Import existing functionality
try:
    from tools.timecode_synchronizer import (
        ffprobe_metadata,
        parse_timecode_to_seconds,
        parse_timestamp_from_filename,
        group_videos_by_trial,
        auto_synchronize_videos
    )
except ImportError:
    # Fallback for testing - define dummy functions
    def ffprobe_metadata(video_path):
        raise RuntimeError("tools.timecode_synchronizer not available")
    
    def parse_timecode_to_seconds(timecode_str, fps=30):
        raise RuntimeError("tools.timecode_synchronizer not available")
    
    def parse_timestamp_from_filename(filename):
        raise RuntimeError("tools.timecode_synchronizer not available")
    
    def group_videos_by_trial(video_files):
        raise RuntimeError("tools.timecode_synchronizer not available")
    
    def auto_synchronize_videos(trial_name, video_paths):
        raise RuntimeError("tools.timecode_synchronizer not available")


class TimecodeSyncEngine:
    """
    Timecode-based synchronization engine
    
    Uses ffprobe to extract metadata and automatically calculate
    frame offsets for video synchronization.
    """
    
    def __init__(self, time_tolerance: int = 5):
        """
        Initialize timecode sync engine
        
        Args:
            time_tolerance: Time tolerance in seconds for grouping videos into trials
        """
        self.time_tolerance = time_tolerance
    
    def sync_trial(self, video_paths: List[str]) -> Dict[str, Any]:
        """
        Synchronize videos in a single trial
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Dictionary with synchronization data:
            {
                "reference_video": str,
                "start_frame_on_reference_video": int,
                "end_frame_on_reference_video": int,
                "offsets": {video_path: frame_offset}
            }
        """
        if not video_paths:
            raise ValueError("No video paths provided")
        
        try:
            # Use existing auto_synchronize_videos function
            trial_name = "single_trial"  # Not used in auto_synchronize_videos
            result = auto_synchronize_videos(trial_name, video_paths)
            return result
            
        except Exception as e:
            raise RuntimeError(f"Timecode synchronization failed: {e}")
    
    def sync_multiple_trials(self, video_folder: str, output_dir: str | None = None) -> Dict[str, Any]:
        """
        Synchronize multiple trials from a video folder
        
        Args:
            video_folder: Path to folder containing videos
            output_dir: Output directory for results (optional)
            
        Returns:
            Dictionary with all trial synchronization data
        """
        video_folder = Path(video_folder)
        
        if not video_folder.exists():
            raise ValueError(f"Video folder not found: {video_folder}")
        
        # Find all video files
        video_files = list(video_folder.glob("*.mp4"))
        if not video_files:
            raise ValueError(f"No MP4 files found in {video_folder}")
        
        # Group videos by trial
        trials = group_videos_by_trial(video_files)
        
        all_trials_data = {}
        
        for trial in trials:
            trial_videos = [str(v[0]) for v in trial]  # Extract file paths
            trial_name = trial[0][1].strftime("%Y%m%d_%H%M%S")  # Use timestamp as name
            
            try:
                trial_data = self.sync_trial(trial_videos)
                all_trials_data[trial_name] = trial_data
                
            except Exception as e:
                print(f"Warning: Failed to sync trial {trial_name}: {e}")
                continue
        
        # Save results if output directory specified
        if output_dir:
            self._save_sync_results(all_trials_data, video_folder, output_dir)
        
        return all_trials_data
    
    def _save_sync_results(self, trials_data: Dict[str, Any], video_folder: Path, output_dir: str):
        """
        Save synchronization results to files
        
        Args:
            trials_data: Synchronization data for all trials
            video_folder: Original video folder path
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_path = output_path / "output.json"
        with open(json_path, "w") as f:
            json.dump(trials_data, f, indent=2)
        
        # Save CSV
        csv_path = output_path / "video_offsets.csv"
        with open(csv_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "Trial", "Filename", "Creation Time", "Timecode", "FPS", "Offset (frames)"
            ])
            
            for trial_name, trial_data in trials_data.items():
                for filename, offset in trial_data["offsets"].items():
                    try:
                        metadata = ffprobe_metadata(filename)
                        writer.writerow([
                            trial_name,
                            Path(filename).name,
                            metadata["creation_time"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                            metadata["timecode"],
                            round(metadata["fps"], 3),
                            offset
                        ])
                    except Exception as e:
                        print(f"Warning: Could not get metadata for {filename}: {e}")
                        writer.writerow([
                            trial_name,
                            Path(filename).name,
                            "Unknown",
                            "Unknown", 
                            "Unknown",
                            offset
                        ])
        
        print(f"✅ Synchronization results saved to {output_path}")
    
    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Get metadata for a single video
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            metadata = ffprobe_metadata(video_path)
            metadata["timecode_seconds"] = parse_timecode_to_seconds(
                metadata["timecode"], 
                metadata["fps"]
            )
            return metadata
            
        except Exception as e:
            raise RuntimeError(f"Failed to get metadata for {video_path}: {e}")
    
    def validate_videos(self, video_paths: List[str]) -> Dict[str, List[str]]:
        """
        Validate video files for synchronization
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Dictionary with validation results:
            {
                "valid": [list of valid video paths],
                "invalid": [list of invalid video paths with reasons]
            }
        """
        valid_videos = []
        invalid_videos = []
        
        for video_path in video_paths:
            try:
                metadata = self.get_video_metadata(video_path)
                
                # Check required fields
                if not metadata.get("timecode"):
                    invalid_videos.append(f"{video_path}: No timecode metadata")
                elif not metadata.get("creation_time"):
                    invalid_videos.append(f"{video_path}: No creation time metadata")
                else:
                    valid_videos.append(video_path)
                    
            except Exception as e:
                invalid_videos.append(f"{video_path}: {str(e)}")
        
        return {
            "valid": valid_videos,
            "invalid": invalid_videos
        }
