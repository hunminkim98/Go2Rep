import os
import datetime
import re
import json
from moviepy import VideoFileClip
from tqdm import tqdm

# Load the synchronization JSON
def load_synchronization_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def parse_timestamp(filename):
    trial_pattern = re.compile(r"(\d{8}_\d{6})")
    match = trial_pattern.search(filename)
    if match:
        timestamp_str = match.group(1)
        return datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    return None

def group_videos_by_trial(video_files, time_tolerance=5):
    trials = []
    video_data = [(file, parse_timestamp(file)) for file in video_files]
    video_data = [v for v in video_data if v[1] is not None]
    video_data.sort(key=lambda x: x[1])
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

def process_videos(source_dir, target_dir, sync_json=None, convert=False, format_choice='mp4'):
    video_formats = ['.MP4', '.AVI', '.MOV', '.MKV', '.flv']
    video_files = [f for f in os.listdir(source_dir) if any(f.endswith(ext) for ext in video_formats)]
    video_paths = [os.path.join(source_dir, f) for f in video_files]
    
    trials = group_videos_by_trial(video_paths)
    summary = []

    for trial_index, trial in enumerate(trials, start=1):
        trial_name = parse_timestamp(trial[0][0]).strftime("%Y%m%d_%H%M%S")
        trial_target_dir = os.path.join(target_dir, trial_name)
        os.makedirs(trial_target_dir, exist_ok=True)
        print(f"\nProcessing trial {trial_name} with {len(trial)} videos...")

        use_sync_file = input(f"Use synchronization file for trial {trial_name}? (yes/no): ").lower() == 'yes'
        downsample = input(f"Do you want to downsample the videos in this trial? (yes/no): ").lower() == 'yes'
        downsample_rate = 1
        if downsample:
            while True:
                try:
                    downsample_rate = int(input("Keep one frame out of every how many frames? (e.g., 2, 3, 4, 5): "))
                    if downsample_rate >= 1:
                        break
                    else:
                        print("Please enter a value of 1 or greater.")
                except ValueError:
                    print("Invalid input. Please enter an integer.")

        min_frames = float('inf')
        video_data = []

        for video_path, _ in trial:
            try:
                clip = VideoFileClip(video_path)
                frame_count = int(clip.fps * clip.duration)
                min_frames = min(min_frames, frame_count)
                video_data.append((clip, video_path, frame_count))
            except Exception as e:
                print(f"Error loading {video_path}: {e}")

        if use_sync_file and sync_json:
            trial_id = trial_name
            if trial_id in sync_json:
                sync_data = sync_json[trial_id]
                offsets = sync_data['offsets']
                start_ref = sync_data['start_frame_on_reference_video']
                end_ref = sync_data['end_frame_on_reference_video']
                print(f"Using synchronization data for trial {trial_name}...")

                for clip, video_path, _ in video_data:
                    video_name = os.path.splitext(os.path.basename(video_path))[0]
                    offset = offsets.get(video_path, 0)
                    start_frame = int(start_ref + offset)
                    end_frame = int(end_ref + offset)
                    start_time = start_frame / clip.fps
                    end_time = end_frame / clip.fps

                trimmed_clip = clip.subclipped(start_time, end_time)
                
                match = re.search(r'CAMERA(\d+)', video_name)
                camera_name = f"CAMERA{match.group(1)}" if match else "CAMERA_UNKNOWN"
                camera_folder = os.path.join(trial_target_dir, camera_name)
                os.makedirs(camera_folder, exist_ok=True)
                video_out_name = camera_name
                output_path = os.path.join(camera_folder, f"{video_out_name}.{format_choice}")
                
                output_fps = clip.fps / downsample_rate if downsample else clip.fps
                print(f"Exporting {video_out_name} to {output_path}...")
                trimmed_clip.write_videofile(output_path, codec='libx264', fps=output_fps, audio=False)
                clip.close()
            else:
                print(f"No synchronization data found for {trial_name}. Skipping sync.")
        else:
            print(f"Trimming {trial_name} to {min_frames} frames.")

            trial_summary = {
                "trial": trial_name,
                "num_videos": len(trial),
                "original_frames": [data[2] for data in video_data],
                "trimmed_frames": min_frames
            }
            summary.append(trial_summary)

            for clip, video_path, _ in video_data:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                end_time = min_frames / clip.fps
                trimmed_clip = clip.subclipped(0, end_time)
                match = re.search(r'CAMERA(\d+)', video_name)
                camera_name = f"CAMERA{match.group(1)}" if match else "CAMERA_UNKNOWN"
                camera_folder = os.path.join(trial_target_dir, camera_name)
                os.makedirs(camera_folder, exist_ok=True)
                output_name = camera_name
                output_path = os.path.join(camera_folder, f"{output_name}.{format_choice}")
                output_fps = clip.fps / downsample_rate if downsample else clip.fps
                print(f"Exporting {output_name} to {output_path}...")
                trimmed_clip.write_videofile(output_path, codec='libx264', fps=output_fps, audio=False)
                # trimmed_clip.write_videofile(output_path, codec='libx264', fps=clip.fps / downsample_rate if downsample else clip.fps, audio=False)
                clip.close()

    print("\nSummary of Processed Trials:")
    for trial in summary:
        print(f"{trial['trial']}: {trial['num_videos']} videos, Original Frames: {trial['original_frames']}, Trimmed Frames: {trial['trimmed_frames']}")
    print("All trials have been processed.")

# Main execution
source_dir = r'C:\videos\DCIM\1'
target_dir = r'D:\Theia\Go_Pro_Extrinsic_Calibration_Videos\NineCam_Gymnase_A1_10042025\Classified\1'
sync_file_path = r'C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Manual_Synchronizer\output.json'

os.makedirs(target_dir, exist_ok=True)
sync_json = load_synchronization_json(sync_file_path)

convert_videos = input("Do you want to convert the videos? (yes/no): ").lower() == 'yes'
format_choice = 'avi' if not convert_videos else input("Choose format (avi/mp4/mov/mkv/flv): ").lower()

process_videos(source_dir, target_dir, sync_json=sync_json, convert=convert_videos, format_choice=format_choice)
