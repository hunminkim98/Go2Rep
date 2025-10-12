"""
Manual video synchronization engine for Go2Rep v2.0

This module provides manual synchronization capabilities with both
interactive and simulation modes for testing without real videos.
"""

import json
import cv2
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import random

# Import existing functionality
try:
    from tools.manual_synchronizer import (
        open_video,
        find_reference_video,
        navigate_and_select_range,
        navigate_frames,
        group_videos_by_trial,
        parse_timestamp
    )
except ImportError:
    # Fallback for testing - define dummy functions
    def open_video(video_path):
        raise RuntimeError("tools.manual_synchronizer not available")
    
    def find_reference_video(video_paths):
        raise RuntimeError("tools.manual_synchronizer not available")
    
    def navigate_and_select_range(video_capture, win_name="Select Frame Range"):
        raise RuntimeError("tools.manual_synchronizer not available")
    
    def navigate_frames(video_capture, win_name="Select Reference Frame", start_frame=0, end_frame=None, reference_frame=None):
        raise RuntimeError("tools.manual_synchronizer not available")
    
    def group_videos_by_trial(video_files, convention):
        raise RuntimeError("tools.manual_synchronizer not available")
    
    def parse_timestamp(filename, filename_convention):
        raise RuntimeError("tools.manual_synchronizer not available")


class ManualSyncEngine:
    """
    Manual synchronization engine
    
    Provides interactive frame selection for manual synchronization
    with simulation mode for testing without real videos.
    """
    
    def __init__(self, 
                 simulate: bool = False, 
                 sample_json: str | None = None,
                 filename_convention: int = 1):
        """
        Initialize manual sync engine
        
        Args:
            simulate: If True, use simulation mode (no real video interaction)
            sample_json: Path to sample JSON file for simulation mode
            filename_convention: Filename convention (1=GoPro, 2=CAMERA)
        """
        self.simulate = simulate
        self.sample_json = sample_json
        self.filename_convention = filename_convention
        
        # Load sample data if provided
        self.sample_data = None
        if sample_json and Path(sample_json).exists():
            with open(sample_json, 'r') as f:
                self.sample_data = json.load(f)
    
    def sync_trial(self, video_paths: List[str]) -> Dict[str, Any]:
        """
        Synchronize videos in a single trial
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Dictionary with synchronization data
        """
        if not video_paths:
            raise ValueError("No video paths provided")
        
        if self.simulate:
            return self._simulate_sync(video_paths)
        else:
            return self._interactive_sync(video_paths)
    
    def _simulate_sync(self, video_paths: List[str]) -> Dict[str, Any]:
        """
        Simulate synchronization without real video interaction
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Simulated synchronization data
        """
        # Use sample data if available
        if self.sample_data:
            # Find matching trial in sample data
            for trial_name, trial_data in self.sample_data.items():
                # Check if any video paths match
                sample_paths = list(trial_data["offsets"].keys())
                if any(path in sample_paths for path in video_paths):
                    return trial_data
        
        # Generate simulated data
        reference_path = video_paths[0]  # Use first video as reference
        
        # Generate random but realistic offsets
        offsets = {reference_path: 0}  # Reference has 0 offset
        
        for i, video_path in enumerate(video_paths[1:], 1):
            # Generate offset between -300 and 300 frames (realistic range)
            offset = random.randint(-300, 300)
            offsets[video_path] = offset
        
        # Generate frame range
        start_frame = random.randint(0, 100)
        end_frame = start_frame + random.randint(1000, 5000)
        
        return {
            "reference_video": reference_path,
            "start_frame_on_reference_video": start_frame,
            "end_frame_on_reference_video": end_frame,
            "offsets": offsets
        }
    
    def _interactive_sync(self, video_paths: List[str]) -> Dict[str, Any]:
        """
        Perform interactive synchronization with real video files
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Synchronization data from interactive process
        """
        # Import here to avoid dependency issues
        from tools.manual_synchronizer import synchronize_videos
        
        try:
            trial_name = "interactive_trial"
            result = synchronize_videos(trial_name, video_paths)
            return result
            
        except Exception as e:
            raise RuntimeError(f"Interactive synchronization failed: {e}")
    
    def sync_multiple_trials(self, 
                           video_folder: str, 
                           output_dir: str | None = None,
                           filename_convention: int | None = None) -> Dict[str, Any]:
        """
        Synchronize multiple trials from a video folder
        
        Args:
            video_folder: Path to folder containing videos
            output_dir: Output directory for results (optional)
            filename_convention: Filename convention override
            
        Returns:
            Dictionary with all trial synchronization data
        """
        video_folder = Path(video_folder)
        
        if not video_folder.exists():
            raise ValueError(f"Video folder not found: {video_folder}")
        
        # Find all video files
        video_files = list(video_folder.glob("*.MP4"))  # GoPro uses uppercase
        if not video_files:
            raise ValueError(f"No MP4 files found in {video_folder}")
        
        # Use provided convention or instance default
        convention = filename_convention if filename_convention is not None else self.filename_convention
        
        # Group videos by trial
        trials = group_videos_by_trial(video_files, convention)
        
        all_trials_data = {}
        
        for trial in trials:
            trial_videos = [str(v[0]) for v in trial]  # Extract file paths
            trial_name = parse_timestamp(trial[0][0], convention).strftime("%Y%m%d_%H%M%S")
            
            try:
                trial_data = self.sync_trial(trial_videos)
                all_trials_data[trial_name] = trial_data
                
            except Exception as e:
                print(f"Warning: Failed to sync trial {trial_name}: {e}")
                continue
        
        # Save results if output directory specified
        if output_dir:
            self._save_sync_results(all_trials_data, output_dir)
        
        return all_trials_data
    
    def _save_sync_results(self, trials_data: Dict[str, Any], output_dir: str):
        """
        Save synchronization results to JSON file
        
        Args:
            trials_data: Synchronization data for all trials
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_path = output_path / "output.json"
        with open(json_path, "w") as f:
            json.dump(trials_data, f, indent=2)
        
        print(f"✅ Manual synchronization results saved to {json_path}")
    
    def validate_videos(self, video_paths: List[str]) -> Dict[str, List[str]]:
        """
        Validate video files for manual synchronization
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Dictionary with validation results
        """
        valid_videos = []
        invalid_videos = []
        
        for video_path in video_paths:
            try:
                # Check if file exists and is readable
                if not Path(video_path).exists():
                    invalid_videos.append(f"{video_path}: File not found")
                    continue
                
                # Try to open video
                cap = open_video(video_path)
                if cap is None:
                    invalid_videos.append(f"{video_path}: Cannot open video file")
                    continue
                
                # Check if video has frames
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if frame_count <= 0:
                    invalid_videos.append(f"{video_path}: No frames found")
                    cap.release()
                    continue
                
                cap.release()
                valid_videos.append(video_path)
                
            except Exception as e:
                invalid_videos.append(f"{video_path}: {str(e)}")
        
        return {
            "valid": valid_videos,
            "invalid": invalid_videos
        }
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get basic information about a video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            cap = open_video(video_path)
            if cap is None:
                raise ValueError("Cannot open video file")
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                "path": video_path,
                "frame_count": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration": duration
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get video info for {video_path}: {e}")
    
    def set_simulation_mode(self, simulate: bool, sample_json: str | None = None):
        """
        Enable or disable simulation mode
        
        Args:
            simulate: Whether to use simulation mode
            sample_json: Path to sample JSON file for simulation
        """
        self.simulate = simulate
        self.sample_json = sample_json
        
        # Reload sample data if provided
        self.sample_data = None
        if sample_json and Path(sample_json).exists():
            with open(sample_json, 'r') as f:
                self.sample_data = json.load(f)
