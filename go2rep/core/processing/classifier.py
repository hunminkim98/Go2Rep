"""
Video classifier for Go2Rep v2.0

This module provides functionality to classify and group videos
by trial based on filename timestamps.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class VideoClassifier:
    """
    Video classifier for grouping videos by trial
    
    Groups videos based on filename timestamps with configurable
    time tolerance for trial grouping.
    """
    
    def __init__(self, time_tolerance: int = 8):
        """
        Initialize video classifier
        
        Args:
            time_tolerance: Time tolerance in seconds for grouping videos into trials
        """
        self.time_tolerance = time_tolerance
    
    def parse_timestamp(self, filename: str, filename_convention: int = 1) -> Optional[datetime]:
        """
        Extract timestamp from filename
        
        Args:
            filename: Video filename
            filename_convention: Convention type (1=GoPro, 2=CAMERA)
            
        Returns:
            Parsed datetime or None if not found
        """
        if filename_convention == 1:  # GoPro format: YYYYMMDD_HHMMSS-GoPro1234-
            pattern = re.compile(r"(\d{8}_\d{6})-GoPro\d+-")
        elif filename_convention == 2:  # CAMERA format: YYYYMMDD_HHMMSS-CAMERA1234-
            pattern = re.compile(r"(\d{8}_\d{6})-CAMERA\d+-")
        else:
            return None
        
        match = pattern.search(filename)
        if match:
            timestamp_str = match.group(1)
            try:
                return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except ValueError:
                return None
        
        return None
    
    def group_videos_by_trial(self, 
                            video_files: List[Path], 
                            filename_convention: int = 1) -> List[List[Tuple[Path, datetime]]]:
        """
        Group videos into trials based on timestamps
        
        Args:
            video_files: List of video file paths
            filename_convention: Filename convention (1=GoPro, 2=CAMERA)
            
        Returns:
            List of trials, where each trial is a list of (file_path, timestamp) tuples
        """
        # Extract timestamps and sort videos by timestamp
        video_data = []
        for file_path in video_files:
            timestamp = self.parse_timestamp(file_path.name, filename_convention)
            if timestamp is not None:
                video_data.append((file_path, timestamp))
        
        # Sort by timestamp
        video_data.sort(key=lambda x: x[1])
        
        # Group videos into trials
        trials = []
        current_trial = []
        
        for file_path, timestamp in video_data:
            if not current_trial:
                current_trial.append((file_path, timestamp))
            else:
                last_timestamp = current_trial[-1][1]
                time_diff = abs((timestamp - last_timestamp).total_seconds())
                
                if time_diff <= self.time_tolerance:
                    current_trial.append((file_path, timestamp))
                else:
                    trials.append(current_trial)
                    current_trial = [(file_path, timestamp)]
        
        if current_trial:
            trials.append(current_trial)
        
        return trials
    
    def classify_videos(self, 
                       video_folder: str, 
                       filename_convention: int = 1) -> Dict[str, List[str]]:
        """
        Classify videos in a folder by trial
        
        Args:
            video_folder: Path to folder containing videos
            filename_convention: Filename convention (1=GoPro, 2=CAMERA)
            
        Returns:
            Dictionary mapping trial names to lists of video paths
        """
        video_folder = Path(video_folder)
        
        if not video_folder.exists():
            raise ValueError(f"Video folder not found: {video_folder}")
        
        # Find all video files
        video_files = list(video_folder.glob("*.MP4"))  # GoPro uses uppercase
        if not video_files:
            raise ValueError(f"No MP4 files found in {video_folder}")
        
        # Group videos by trial
        trials = self.group_videos_by_trial(video_files, filename_convention)
        
        # Convert to dictionary format
        classified_videos = {}
        
        for trial in trials:
            if not trial:
                continue
            
            # Use timestamp of first video as trial name
            trial_name = trial[0][1].strftime("%Y%m%d_%H%M%S")
            video_paths = [str(file_path) for file_path, _ in trial]
            classified_videos[trial_name] = video_paths
        
        return classified_videos
    
    def get_trial_info(self, trial_videos: List[Tuple[Path, datetime]]) -> Dict[str, any]:
        """
        Get information about a trial
        
        Args:
            trial_videos: List of (file_path, timestamp) tuples for a trial
            
        Returns:
            Dictionary with trial information
        """
        if not trial_videos:
            return {}
        
        # Sort by timestamp
        trial_videos.sort(key=lambda x: x[1])
        
        first_video, first_timestamp = trial_videos[0]
        last_video, last_timestamp = trial_videos[-1]
        
        duration = (last_timestamp - first_timestamp).total_seconds()
        
        return {
            "trial_name": first_timestamp.strftime("%Y%m%d_%H%M%S"),
            "start_time": first_timestamp,
            "end_time": last_timestamp,
            "duration_seconds": duration,
            "video_count": len(trial_videos),
            "first_video": str(first_video),
            "last_video": str(last_video),
            "all_videos": [str(file_path) for file_path, _ in trial_videos]
        }
    
    def validate_videos(self, 
                      video_folder: str, 
                      filename_convention: int = 1) -> Dict[str, List[str]]:
        """
        Validate videos in a folder
        
        Args:
            video_folder: Path to folder containing videos
            filename_convention: Filename convention (1=GoPro, 2=CAMERA)
            
        Returns:
            Dictionary with validation results:
            {
                "valid": [list of valid video paths],
                "invalid": [list of invalid video paths with reasons]
            }
        """
        video_folder = Path(video_folder)
        
        if not video_folder.exists():
            return {
                "valid": [],
                "invalid": [f"Folder not found: {video_folder}"]
            }
        
        # Find all video files
        video_files = list(video_folder.glob("*.MP4"))
        
        valid_videos = []
        invalid_videos = []
        
        for video_file in video_files:
            try:
                # Check if file exists and is readable
                if not video_file.exists():
                    invalid_videos.append(f"{video_file}: File not found")
                    continue
                
                # Check file size
                file_size = video_file.stat().st_size
                if file_size == 0:
                    invalid_videos.append(f"{video_file}: Empty file")
                    continue
                
                # Check filename format
                timestamp = self.parse_timestamp(video_file.name, filename_convention)
                if timestamp is None:
                    invalid_videos.append(f"{video_file}: Invalid filename format")
                    continue
                
                valid_videos.append(str(video_file))
                
            except Exception as e:
                invalid_videos.append(f"{video_file}: {str(e)}")
        
        return {
            "valid": valid_videos,
            "invalid": invalid_videos
        }
    
    def get_video_statistics(self, video_folder: str) -> Dict[str, any]:
        """
        Get statistics about videos in a folder
        
        Args:
            video_folder: Path to folder containing videos
            
        Returns:
            Dictionary with video statistics
        """
        video_folder = Path(video_folder)
        
        if not video_folder.exists():
            return {}
        
        # Find all video files
        video_files = list(video_folder.glob("*.MP4"))
        
        if not video_files:
            return {
                "total_videos": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }
        
        total_size = sum(file.stat().st_size for file in video_files)
        
        return {
            "total_videos": len(video_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_size_mb": round(total_size / (1024 * 1024) / len(video_files), 2)
        }
