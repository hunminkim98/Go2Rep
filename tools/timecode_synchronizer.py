import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime
import re
import os

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
    fps = eval(fps_str)

    return {
        "filename": str(video_path),
        "creation_time": datetime.fromisoformat(creation_time),
        "timecode": timecode,
        "fps": fps,
        "nb_frames": video_stream.get("nb_frames")
    }

def parse_timecode_to_seconds(timecode_str, fps=30):
    try:
        sep = ';' if ';' in timecode_str else ':'
        hh, mm, ss, ff = map(int, timecode_str.replace(';', ':').split(':'))
        return hh * 3600 + mm * 60 + ss + ff / fps
    except Exception as e:
        print(f"⚠️ Failed to parse timecode '{timecode_str}': {e}")
        return None

def parse_timestamp_from_filename(filename):
    match = re.search(r"(\d{8}_\d{6})", filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
        except:
            return None
    return None

def group_videos_by_trial(video_files, time_tolerance=5):
    videos_with_time = [(f, parse_timestamp_from_filename(f.name)) for f in video_files]
    videos_with_time = [v for v in videos_with_time if v[1] is not None]
    videos_with_time.sort(key=lambda x: x[1])

    trials = []
    current_trial = []

    for video, ts in videos_with_time:
        if not current_trial:
            current_trial.append((video, ts))
        else:
            last_ts = current_trial[-1][1]
            if abs((ts - last_ts).total_seconds()) <= time_tolerance:
                current_trial.append((video, ts))
            else:
                trials.append(current_trial)
                current_trial = [(video, ts)]
    if current_trial:
        trials.append(current_trial)
    return trials

def auto_synchronize_videos(trial_name, video_paths):
    all_data = []
    for video_path in video_paths:
        try:
            data = ffprobe_metadata(video_path)
            data["timecode_seconds"] = parse_timecode_to_seconds(data["timecode"], data["fps"])
            all_data.append(data)
        except Exception as e:
            print(f"❌ Error reading metadata from {video_path}: {e}")

    all_data.sort(key=lambda x: x["creation_time"])

    ref = all_data[0]
    reference_time = ref["timecode_seconds"]
    reference_video = ref["filename"]

    offsets = {}
    for entry in all_data:
        delta_seconds = entry["timecode_seconds"] - reference_time
        frame_offset = round(delta_seconds * entry["fps"])
        offsets[entry["filename"]] = frame_offset

    ref_nb_frames = None
    try:
        ref_nb_frames = int(ref["nb_frames"])
    except:
        print(f"⚠️ Could not determine number of frames in reference video: {reference_video}")

    return {
        "reference_video": reference_video,
        "start_frame_on_reference_video": 0,
        "end_frame_on_reference_video": ref_nb_frames if ref_nb_frames else 99999,
        "offsets": offsets
    }


# def timecode_synchronizer(video_folder, output_json_path="output_grouped_auto_sync.json", output_csv_path="video_offsets.csv"):
    # """
    # Main callable function to perform timecode synchronization from a GUI or script.
    # """
    # video_folder = Path(video_folder)
    # video_files = list(video_folder.glob("*.mp4"))
    # trials = group_videos_by_trial(video_files)

    # all_trials_data = {}

    # with open(output_csv_path, "w", newline="") as csv_file:
        # writer = csv.writer(csv_file)
        # writer.writerow(["Trial", "Filename", "Creation Time", "Timecode", "FPS", "Offset (frames)"])

        # for trial in trials:
            # trial_videos = [v[0] for v in trial]
            # trial_name = trial[0][1].strftime("%Y%m%d_%H%M%S")
            # print(f"\n🚀 Processing trial: {trial_name}")
            # trial_data = auto_synchronize_videos(trial_name, trial_videos)
            # all_trials_data[trial_name] = trial_data

            # for filename, offset in trial_data["offsets"].items():
                # metadata = ffprobe_metadata(filename)
                # writer.writerow([
                    # trial_name,
                    # Path(filename).name,
                    # metadata["creation_time"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                    # metadata["timecode"],
                    # round(metadata["fps"], 3),
                    # offset
                # ])

    # with open(output_json_path, "w") as f:
        # json.dump(all_trials_data, f, indent=4)

    # print(f"✅ All trials processed and saved to {output_json_path}")

def timecode_synchronizer(video_folder, theia_folder, filename_convention=1):
    """
    Main callable function to perform timecode synchronization from a GUI or script.
    Saves outputs (CSV and JSON) in the Synchronisation subfolder of the theia_folder.
    """
    video_folder = Path(video_folder)
    video_files = list(video_folder.glob("*.mp4"))
    trials = group_videos_by_trial(video_files)

    all_trials_data = {}

    # ✅ Create Synchronisation directory under Theia folder if it doesn't exist
    sync_dir = Path(theia_folder) / "Synchronisation"
    sync_dir.mkdir(parents=True, exist_ok=True)

    # ✅ Define full paths to output files within sync_dir
    output_json_path = sync_dir / "output.json"
    output_csv_path = sync_dir / "video_offsets.csv"

    with open(output_csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Trial", "Filename", "Creation Time", "Timecode", "FPS", "Offset (frames)"])

        for trial in trials:
            trial_videos = [v[0] for v in trial]
            trial_name = trial[0][1].strftime("%Y%m%d_%H%M%S")
            print(f"\n🚀 Processing trial: {trial_name}")
            trial_data = auto_synchronize_videos(trial_name, trial_videos)
            all_trials_data[trial_name] = trial_data

            for filename, offset in trial_data["offsets"].items():
                metadata = ffprobe_metadata(filename)
                writer.writerow([
                    trial_name,
                    Path(filename).name,
                    metadata["creation_time"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                    metadata["timecode"],
                    round(metadata["fps"], 3),
                    offset
                ])

    with open(output_json_path, "w") as f:
        json.dump(all_trials_data, f, indent=4)

    print(f"✅ All trials processed and saved to {output_json_path}")  
    
