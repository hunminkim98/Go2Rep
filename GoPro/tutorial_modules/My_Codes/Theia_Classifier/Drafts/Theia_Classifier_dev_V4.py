import os
import datetime
import re
import cv2
from moviepy import VideoFileClip

def parse_timestamp(filename):
    """Extracts and converts timestamp from filename to a datetime object."""
    trial_pattern = re.compile(r"(\d{8}_\d{6})")  # Adjust based on your filename structure
    match = trial_pattern.search(filename)
    if match:
        timestamp_str = match.group(1)  # Example: "20250324_094909"
        return datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    return None

def group_videos_by_trial(video_files, time_tolerance=5):
    """Groups videos into trials allowing a ±time_tolerance seconds difference."""
    trials = []
    video_data = [(file, parse_timestamp(file)) for file in video_files]
    video_data = [v for v in video_data if v[1] is not None]  # Remove invalid timestamps
    video_data.sort(key=lambda x: x[1])  # Sort by timestamp
    
    current_trial = []
    for i, (video, timestamp) in enumerate(video_data):
        if not current_trial:
            current_trial.append((video, timestamp))
        else:
            last_timestamp = current_trial[-1][1]
            if abs((timestamp - last_timestamp).total_seconds()) <= time_tolerance:
                current_trial.append((video, timestamp))
            else:
                trials.append(current_trial)
                current_trial = [(video, timestamp)]
    
    if current_trial:
        trials.append(current_trial)
    
    return trials

def process_videos(source_dir, target_dir, convert=False, format_choice='mp4'):
    """Processes all video trials in the given directory and provides a summary."""
    video_formats = ['.MP4', '.AVI', '.MOV', '.MKV', '.flv']
    video_files = [f for f in os.listdir(source_dir) if any(f.endswith(ext) for ext in video_formats)]
    video_paths = [os.path.join(source_dir, f) for f in video_files]
    
    trials = group_videos_by_trial(video_paths)
    summary = []
    for trial_index, trial in enumerate(trials, start=1):
        trial_name = f"Trial_{trial_index}"
        trial_target_dir = os.path.join(target_dir, trial_name)
        os.makedirs(trial_target_dir, exist_ok=True)
        
        print(f"Processing {trial_name} with {len(trial)} videos...")
        min_frames = float('inf')
        video_data = []
        
        for video_path, _ in trial:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            match = re.search(r'CAMERA(\d+)', video_name)
            if match:
                camera_name = f"CAMERA{match.group(1)}"
            camera_folder = os.path.join(trial_target_dir, camera_name)
            os.makedirs(camera_folder, exist_ok=True)
            output_path = os.path.join(camera_folder, f"{video_name}.{format_choice}" if convert else video_name)
            try:
                clip = VideoFileClip(video_path)
                frame_count = int(clip.fps * clip.duration)
                min_frames = min(min_frames, frame_count)
                video_data.append((clip, output_path, frame_count))
            except Exception as e:
                print(f"Error processing {video_path}: {e}")

        print(f"Trimming {trial_name} to {min_frames} frames.")
        trial_summary = {
            "trial": trial_name,
            "num_videos": len(trial),
            "original_frames": [data[2] for data in video_data],  # Frame count of each video
            "trimmed_frames": min_frames
        }
        summary.append(trial_summary)
        
        
        for clip, output_path, _ in video_data:
            trimmed_clip = clip.subclipped(0, min_frames / clip.fps)
            output_path=re.sub(r'[^\\]+-(CAMERA\d+)-[^\\]+\.mp4$', r'\1.mp4', output_path)
            trimmed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            trimmed_clip.close()
            clip.close()
    
    print("\nSummary of Processed Trials:")
    for trial in summary:
        print(f"{trial['trial']}: {trial['num_videos']} videos, Original Frames: {trial['original_frames']}, Trimmed Frames: {trial['trimmed_frames']}")
    
    print("All trials have been processed.")
# Main execution
source_dir = r'C:\videos\DCIM\1'
target_dir = r'C:\videos\DCIM\3'
os.makedirs(target_dir, exist_ok=True)

convert_videos = input("Do you want to convert the videos? (yes/no)").lower() == 'yes'
format_choice = 'avi' if not convert_videos else input("Choose format (avi/mp4/mov/mkv/flv): ").lower()

process_videos(source_dir, target_dir, convert=convert_videos, format_choice=format_choice)
