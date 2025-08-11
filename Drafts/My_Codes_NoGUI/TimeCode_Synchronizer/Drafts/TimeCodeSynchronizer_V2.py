import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime


def ffprobe_metadata(video_path):
    command = [
        "ffprobe", "-v", "error", "-show_streams", "-select_streams", "v",
        "-of", "json", str(video_path)
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = json.loads(result.stdout)

    video_stream = next(stream for stream in metadata['streams'] if stream['codec_type'] == 'video')

    creation_time = video_stream['tags']['creation_time'].rstrip('Z')
    timecode = video_stream['tags'].get('timecode')
    fps_str = video_stream.get("avg_frame_rate", "30/1")
    fps = eval(fps_str)  # e.g. "30000/1001" → 29.97

    return {
        "filename": str(video_path),
        "creation_time": datetime.fromisoformat(creation_time),
        "timecode": timecode,
        "fps": fps
    }


def parse_timecode_to_seconds(timecode_str, fps=30):
    # Format: HH:MM:SS;FF or HH:MM:SS:FF
    try:
        sep = ';' if ';' in timecode_str else ':'
        hh, mm, ss, ff = map(int, timecode_str.replace(';', ':').split(':'))
        return hh * 3600 + mm * 60 + ss + ff / fps
    except Exception as e:
        print(f"⚠️ Failed to parse timecode '{timecode_str}': {e}")
        return None


def auto_synchronize_videos_using_timecodes(video_folder, trial_name, output_json_path, output_csv_path):
    video_files = sorted(Path(video_folder).glob("*.mp4"))

    all_data = []
    for video_path in video_files:
        try:
            data = ffprobe_metadata(video_path)
            data["timecode_seconds"] = parse_timecode_to_seconds(data["timecode"], data["fps"])
            all_data.append(data)
        except Exception as e:
            print(f"❌ Error reading metadata from {video_path}: {e}")

    # Sort videos by creation time (or switch to timecode_seconds for finer alignment)
    all_data.sort(key=lambda x: x["creation_time"])

    # First video is reference
    ref = all_data[0]
    reference_time = ref["timecode_seconds"]
    reference_video = ref["filename"]

    # Compute frame offsets
    offsets = {}
    for entry in all_data:
        delta_seconds = entry["timecode_seconds"] - reference_time
        frame_offset = round(delta_seconds * entry["fps"])
        offsets[entry["filename"]] = frame_offset

    # Build output JSON
    json_output = {
        trial_name: {
            "reference_video": reference_video,
            "start_frame_on_reference_video": 0,
            "end_frame_on_reference_video": 99999,
            "offsets": offsets
        }
    }

    # Save JSON
    with open(output_json_path, "w") as f:
        json.dump(json_output, f, indent=4)

    # Save CSV
    with open(output_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Creation Time", "Timecode", "FPS", "Offset (frames)"])
        for entry in all_data:
            writer.writerow([
                Path(entry["filename"]).name,
                entry["creation_time"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                entry["timecode"],
                round(entry["fps"], 3),
                offsets[entry["filename"]]
            ])

    print(f"✅ Synchronized {len(all_data)} videos.")
    print(f"📄 JSON saved to: {output_json_path}")
    print(f"📄 CSV saved to:  {output_csv_path}")

    return json_output

if __name__ == "__main__":
    trial_name = "20250617_153000"  # or derive from filename
    folder = "C:/videos/DCIM/3"
    json_path = "output_auto_sync.json"
    csv_path = "video_offsets.csv"

    auto_synchronize_videos_using_timecodes(folder, trial_name, json_path, csv_path)