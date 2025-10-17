import os
import datetime
import re
import cv2
import json
from moviepy import VideoFileClip

# Load the synchronization JSON
def load_synchronization_json(file_path):
    """Loads the synchronization JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

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

def process_videos(source_dir, target_dir, sync_json=None, convert=False, format_choice='mp4'):
    """Processes all video trials in the given directory and provides a summary."""
    video_formats = ['.MP4', '.AVI', '.MOV', '.MKV', '.flv','.mp4']
    video_files = [f for f in os.listdir(source_dir) if any(f.endswith(ext) for ext in video_formats)]
    video_paths = [os.path.join(source_dir, f) for f in video_files]
    
    trials = group_videos_by_trial(video_paths)
    summary = []
    
    for trial_index, trial in enumerate(trials, start=1):
        trial_name = parse_timestamp(trial[0][0]).strftime("%Y%m%d_%H%M%S")
        trial_target_dir = os.path.join(target_dir, trial_name)
        os.makedirs(trial_target_dir, exist_ok=True)
        # Ask user whether to use the synchronization file or not
        print(f"Processing {trial_name} with {len(trial)} videos...")
        print(f"\nFor the trial {trial_name} ...")
        use_sync_file = input("Do you want to use the synchronization file for cutting videos? (yes/no): ").lower() == 'yes'
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
            
            if not use_sync_file:
                try:
                    clip = VideoFileClip(video_path)
                    frame_count = int(clip.fps * clip.duration)
                    min_frames = min(min_frames, frame_count)
                    video_data.append((clip, output_path, frame_count))
                except Exception as e:
                    print(f"Error processing {video_path}: {e}")
        
        
        if use_sync_file and sync_json:
            trial_id = trial_name
            if trial_id in sync_json:
                sync_data = sync_json[trial_id]
                offsets = sync_data['offsets']
                
                # Initialize lists to store frame data for the summary
                frame_summary = []
                
                # Adjust frame cutting based on synchronization offsets
                print("🔍 Pre-checking all videos for trimmed frame counts...\n")
                trimmed_frame_counts = {}
                # First loop — gather trimmed frame counts
                for video_path, _ in trial:
                    video_name = os.path.splitext(os.path.basename(video_path))[0]
                    if video_path in offsets:
                        offset = offsets[video_path]
                        try:
                            clip = VideoFileClip(video_path)
                            start_frame = int(sync_data['start_frame_on_reference_video'] + offset)
                            end_frame = int(sync_data['end_frame_on_reference_video'] + offset)
                            trimmed_clip = clip.subclipped(start_frame / clip.fps, end_frame / clip.fps)
                            total_trimmed_frames = int(trimmed_clip.fps * trimmed_clip.duration)
            
                            trimmed_frame_counts[video_path] = total_trimmed_frames
            
                            clip.close()
                            trimmed_clip.close()
                        except Exception as e:
                            print(f"❌ Error checking frames for {video_path}: {e}")
            
                if not trimmed_frame_counts:
                    print("⚠️ No videos processed in the pre-check. Exiting.")
                    return
            
                min_trimmed_frames = min(trimmed_frame_counts.values())
                print(f"\n✅ Minimum trimmed frame count across all videos: {min_trimmed_frames}\n")
            
                # Second loop — trim, adjust, and save
                for video_path, _ in trial:
                    video_name = os.path.splitext(os.path.basename(video_path))[0]
                    if video_path in offsets:
                        offset = offsets[video_path]
                        try:
                            clip = VideoFileClip(video_path)
                            start_frame = int(sync_data['start_frame_on_reference_video'] + offset)
                            end_frame = int(sync_data['end_frame_on_reference_video'] + offset)
            
                            # Total frames before trimming
                            total_frames_before = int(clip.fps * clip.duration)
            
                            trimmed_clip = clip.subclipped(start_frame / clip.fps, end_frame / clip.fps)
                            total_trimmed_frames = int(trimmed_clip.fps * trimmed_clip.duration)
            
                            # Adjust if this video is longer than the shortest
                            if total_trimmed_frames > min_trimmed_frames:
                                frames_to_cut = total_trimmed_frames - min_trimmed_frames
                                seconds_to_cut = frames_to_cut / clip.fps
                                new_end_time = trimmed_clip.duration - seconds_to_cut
                                trimmed_clip = trimmed_clip.subclipped(0, new_end_time)
                                print(f"⚠️ Adjusted {video_name}: cut {frames_to_cut} frame(s)")
            
                                # Recalculate just in case
                                total_trimmed_frames = int(trimmed_clip.fps * trimmed_clip.duration)
            
                            # Save trimmed video
                            match = re.search(r'CAMERA(\d+)', video_name)
                            if match:
                                camera_name = f"CAMERA{match.group(1)}"
                                camera_folder = os.path.join(trial_target_dir, camera_name)
                                os.makedirs(camera_folder, exist_ok=True)
            
                                video_name_2Save = re.sub(r'.*-(CAMERA\d+)-.*', r'\1', video_name)
                                output_path = os.path.join(camera_folder, f"{video_name_2Save}.{format_choice}" if convert else video_name_2Save)
            
                                trimmed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
                            # Cleanup
                            trimmed_clip.close()
                            clip.close()
            
                            # Record summary
                            frame_summary.append({
                                "video_name": video_name,
                                "total_frames_before": total_frames_before,
                                "total_frames_after": total_trimmed_frames
                            })
            
                        except Exception as e:
                            print(f"❌ Error processing {video_path}: {e}")
            
                # Summary
                print(f"\n📋 Summary of frames for {trial_target_dir} ...")
                for entry in frame_summary:
                    print(f"Video: {entry['video_name']}")
                    print(f"Total frames before trimming: {entry['total_frames_before']}")
                    print(f"Total frames after trimming:  {entry['total_frames_after']}\n")
            else:
                print(f"Error: No synchronization data available for {trial_name}. Using default frame cutting.")
        else:
            # Default behavior: trim to the minimum frame count
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
                output_path = re.sub(r'[^\\]+-(CAMERA\d+)-[^\\]+\.mp4$', r'\1.mp4', output_path)
                trimmed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                trimmed_clip.close()
                clip.close()
    
    print("\nSummary of Processed Trials:")
    for trial in summary:
        print(f"{trial['trial']}: {trial['num_videos']} videos, Original Frames: {trial['original_frames']}, Trimmed Frames: {trial['trimmed_frames']}")
    
    print("All trials have been processed.")

# Main execution
source_dir = r'C:\videos\DCIM\1'
target_dir = r'D:\Theia\Manip_Sprint_premanip_16-04-2025\Classified\2'
sync_file_path = r'C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Manual_Synchronizer\output.json'

os.makedirs(target_dir, exist_ok=True)

# Load synchronization data
sync_json = load_synchronization_json(sync_file_path)

convert_videos = input("Do you want to convert the videos? (yes/no)").lower() == 'yes'
format_choice = 'avi' if not convert_videos else input("Choose format (avi/mp4/mov/mkv/flv): ").lower()

process_videos(source_dir, target_dir, sync_json=sync_json, convert=convert_videos, format_choice=format_choice)
