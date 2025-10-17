import os
import shutil
import glob
import cv2
from moviepy import VideoFileClip

def process_videos(source_dir, target_dir, convert=False, format_choice='avi'):
    video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.MP4', '.AVI', '.MOV', '.MKV', '.FLV']
    video_files = [f for f in os.listdir(source_dir) if any(f.endswith(ext) for ext in video_formats)]
    
    if not video_files:
        print("No video files found.")
        return
    
    min_frames = float('inf')
    video_data = []
    frame_info = []  # List to store frame count information
    trimmed_frame_info = []  # List to store trimmed frame count information
    
    for video in video_files:
        video_path = os.path.join(source_dir, video)
        video_name = os.path.splitext(video)[0]
        target_video_dir = os.path.join(target_dir, video_name)
        
        if not os.path.exists(target_video_dir):
            os.makedirs(target_video_dir)
        
        output_path = os.path.join(target_video_dir, f"{video_name}.{format_choice}" if convert else video)
        
        try:
            clip = VideoFileClip(video_path)
            frame_count = int(clip.fps * clip.duration)
            frame_info.append(f"{video}: {frame_count} frames")  # Store in list
            min_frames = min(min_frames, frame_count)
            video_data.append((clip, output_path, frame_count))
        except Exception as e:
            print(f"Error processing video {video}: {e}")
    # Print all frame counts before trimming
    print("\nFrame counts for each video:")
    print("\n".join(frame_info))
    
    print(f"\nTrimming videos to {min_frames} frames.\n")
    for clip, output_path, frame_count in video_data:
        trimmed_clip = clip.subclipped(0, min_frames / clip.fps)
        trimmed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        trimmed_clip.close()
        clip.close()
        
        # Store trimmed frame count (should be equal to min_frames for all videos)
        trimmed_frame_info.append(f"{os.path.basename(output_path)}: {min_frames} frames")

    # Print both original and trimmed frame counts at the end
    print("\nFrame counts before and after trimming:")
    for original, trimmed in zip(frame_info, trimmed_frame_info):
        print(f"{original} → {trimmed}")
    
    print("\nAll videos have been formatted and trimmed.")

# Main code
source_dir = r'D:\Theia\Go_Pro_Extrinsic_Calibration_Videos\Raw\Manip05-03-2025\Extrinsic\Trial_3'
target_dir = r'D:\Theia\Go_Pro_Extrinsic_Calibration_Videos\NineCam_PPrime_Lab\Trial_3'

if not os.path.exists(target_dir):
    os.makedirs(target_dir)

print("Do you want to convert the videos? (yes/no)")
convert_videos = input().lower() == 'yes'

if convert_videos:
    print("Choose the format to convert all videos to:")
    print("1. AVI (default)")
    print("2. MP4")
    print("3. MOV")
    print("4. MKV")
    print("5. FLV")
    
    format_response = input("Enter the number for the format (default is 1): ").strip()
    format_choice = {'2': 'mp4', '3': 'mov', '4': 'mkv', '5': 'flv'}.get(format_response, 'avi')
else:
    format_choice = None

process_videos(source_dir, target_dir, convert=convert_videos, format_choice=format_choice)