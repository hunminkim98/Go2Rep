import os
import csv
import subprocess
from pathlib import Path
from datetime import datetime
import json

def extract_video_metadata(video_path):
    """
    Extract timecode, creation time, and FPS from a video file using ffprobe.
    """
    try:
        command = [
            "ffprobe", "-v", "error", "-show_streams", "-select_streams", "v",
            "-of", "json", str(video_path)
        ]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        metadata = json.loads(process.stdout)
        video_stream = next(
            stream for stream in metadata['streams'] if stream['codec_type'] == 'video'
        )

        # Extract creation time
        creation_time_str = video_stream['tags']['creation_time'].rstrip("Z")
        starting_time = datetime.fromisoformat(creation_time_str)
        formatted_starting_time = starting_time.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Extract timecode
        timecode = video_stream['tags'].get('timecode', None)

        # Extract FPS
        avg_frame_rate = video_stream.get("avg_frame_rate", "0/0")
        try:
            num, denom = map(int, avg_frame_rate.split('/'))
            fps = round(num / denom, 3) if denom != 0 else 0
        except:
            fps = 0

        return video_path.name, formatted_starting_time, timecode, fps

    except Exception as e:
        print(f"Error processing {video_path}: {e}")
        return video_path.name, "Error", "Error", 0

def save_metadata_to_csv(metadata, output_csv_path): 
    """Save extracted metadata to a CSV file sorted by creation time."""
    sorted_metadata = sorted(metadata, key=lambda x: x[1])
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Filename", "Creation Time", "Timecode", "FPS"])
        writer.writerows(sorted_metadata)

def main():
    video_folder = Path("C:/videos/DCIM/3") 
    output_csv_path = video_folder / "video_metadata.csv"
    
    video_files = list(video_folder.glob("*.mp4"))
    metadata = [extract_video_metadata(video) for video in video_files]
    
    save_metadata_to_csv(metadata, output_csv_path)
    print(f"Metadata saved to {output_csv_path}")

if __name__ == "__main__":
    main()
