import cv2
import os
import numpy as np
import keyboard
import json
from tqdm import tqdm
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import re
import datetime

##to run the code
##Conda activate cudatest 
##"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
##where cl
##nvcc --version
##spyder


# Initialize log list
global log_data
log_data = []

def log_message(message):
    print(message)
    log_data.append(message)

# CUDA kernel
kernel_code = """
__global__ void process_frame(unsigned char *frame, int width, int height) {
    int x = threadIdx.x + blockIdx.x * blockDim.x;
    int y = threadIdx.y + blockIdx.y * blockDim.y;
    if (x < width && y < height) {
        int idx = (y * width + x) * 3;
        frame[idx] = 255 - frame[idx];
    }
}
"""
mod = SourceModule(kernel_code)
process_frame = mod.get_function("process_frame")

# Define frame_cache as a global dictionary
frame_cache = {}

def open_video(video_path):
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found - {video_path}")
        return None
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Unable to open video {video_path}")
        return None
    return cap

def find_reference_video(video_paths):
    min_frames = float('inf')
    reference_path = None
    for video_path in video_paths:
        video = open_video(video_path)
        if video:
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames < min_frames:
                min_frames = total_frames
                reference_path = video_path
            video.release()
    return reference_path, min_frames

def navigate_and_select_range(video_capture, win_name="Select Frame Range"):
    """Allow the user to navigate and select the starting and ending frame interactively."""
    global frame_number, total_frames, video, window_name
    if video_capture is None:
        print("❌ Error: Video is not loaded correctly.")
        return None, None

    video = video_capture
    window_name = win_name
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 0
    selected_frames = []
    if len(selected_frames) == 0: print("Choose the starting frame: ")
    while True:
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = video.read()
        if not ret:
            break

        frame_gpu = cuda.mem_alloc(frame.nbytes)
        cuda.memcpy_htod(frame_gpu, frame)
        
        process_frame(
            frame_gpu,
            np.int32(frame.shape[1]),
            np.int32(frame.shape[0]),
            block=(32, 32, 1),
            grid=(frame.shape[1] // 32 + 1, frame.shape[0] // 32 + 1)
        )

        cuda.memcpy_dtoh(frame, frame_gpu)
        display_frame = cv2.resize(frame, (640, 480))
        cv2.putText(display_frame, f"Frame: {frame_number}/{total_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(0) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            if len(selected_frames) < 2:
                selected_frames.append(frame_number)
                print(f"✅ Frame {frame_number} selected.")
                if len(selected_frames) == 1: print("Choose the ending frame: ")
            if len(selected_frames) == 2:
                return min(selected_frames), max(selected_frames)
        elif key == ord('d'):
            frame_number = min(frame_number + 1, total_frames - 1)
        elif key == ord('a'):
            frame_number = max(0, frame_number - 1)
        elif key == ord('n'):
            try:
                user_input = int(input(f"Enter the frame number (0 - {total_frames - 1}): "))
                if 0 <= user_input < total_frames:
                    frame_number = user_input
                else:
                    print(f"❌ Invalid frame number. Please enter a value between 0 and {total_frames - 1}.")
            except ValueError:
                print("❌ Invalid input. Please enter a valid integer.")
    
    cv2.destroyAllWindows()
    return None, None

def get_frame(video, frame_number):
    """Retrieve a frame from the video, using cache if available."""
    if frame_number in frame_cache:
        return frame_cache[frame_number]

    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    if ret:
        frame_cache[frame_number] = frame  # Cache the frame
    return frame
    
    
def navigate_frames(video_capture, win_name="Select Reference Frame", start_frame=0, end_frame=None, reference_frame=None):
    global frame_number, total_frames, video, window_name
    if video_capture is None:
        print("❌ Error: Video is not loaded correctly.")
        return None

    frame_cache.clear()  # Clear cached frames when a new video starts
    video = video_capture
    window_name = win_name
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = reference_frame if reference_frame is not None else start_frame
    end_frame = end_frame if end_frame is not None else total_frames - 1

    while True:
        frame = get_frame(video, frame_number)  # Use the cached frame
        if frame is None:
            break

        frame_gpu = cuda.mem_alloc(frame.nbytes)
        cuda.memcpy_htod(frame_gpu, frame)
        
        process_frame(
            frame_gpu,
            np.int32(frame.shape[1]),
            np.int32(frame.shape[0]),
            block=(32, 32, 1),
            grid=(frame.shape[1] // 32 + 1, frame.shape[0] // 32 + 1)
        )

        cuda.memcpy_dtoh(frame, frame_gpu)
        display_frame = cv2.resize(frame, (640, 480))
        cv2.putText(display_frame, f"Frame: {frame_number}/{total_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(0) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print(f"✅ Reference frame selected: {frame_number}")
            return frame_number
        elif key == ord('d'):
            frame_number = min(frame_number + 1, end_frame)
        elif key == ord('a'):
            frame_number = max(start_frame, frame_number - 1)          
        elif key == ord('n'):
            try:
                user_input = int(input(f"Enter the frame number ({start_frame} - {end_frame}): "))
                if start_frame <= user_input <= end_frame:
                    frame_number = user_input
                else:
                    print(f"❌ Invalid frame number. Please enter a value between {start_frame} and {end_frame}.")
            except ValueError:
                print("❌ Invalid input. Please enter a valid integer.")
    
    cv2.destroyAllWindows()
    return frame_number

def synchronize_videos(trial_name, video_paths):
    if not video_paths:
        print(f"❌ Error: No video files found for trial {trial_name}.")
        return
    
    reference_path, _ = find_reference_video(video_paths)
    if reference_path is None:
        print(f"❌ Error: No valid reference video found for trial {trial_name}.")
        return
    
    reference_video = open_video(reference_path)
    if reference_video is None:
        return
    
    start_frame, end_frame = navigate_and_select_range(reference_video)
    cv2.destroyAllWindows()
    reference_frame = navigate_frames(reference_video, f"Reference - {trial_name}", start_frame, end_frame)
    reference_video.release()
    if reference_frame is None:
        return
    offsets = {}
    for video_path in video_paths:
        # Only process video paths that are not equal to reference_path
        if video_path != reference_path:
            video = open_video(video_path)
            if video:
                offset = navigate_frames(video, f"Sync {os.path.basename(video_path)}", start_frame, end_frame, reference_frame)
                if offset is not None:
                    offsets[video_path] = offset - reference_frame
                video.release()

    cv2.destroyAllWindows()
    
    # Include start and stop frames in results
    trial_data = {
        "reference_video": reference_path,
        "start_frame_on_reference_video": start_frame,
        "end_frame_on_reference_video": end_frame,
        reference_path: "0",
        "offsets": offsets
    }

    print(f"\n✅ Synchronization completed for trial {trial_name} with offsets:")
    for vid, off in offsets.items():
        log_message(f"{vid}: {off} frames")

    return trial_data


# Adjusted regex pattern to extract timestamps from filenames
trial_pattern = re.compile(r"(\d{8}_\d{6})")

def parse_timestamp(filename):
    """Extracts and converts timestamp from filename to a datetime object."""
    match = trial_pattern.search(filename)
    if match:
        timestamp_str = match.group(1)  # Example: "20250324_094909"
        return datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    return None

def group_videos_by_trial(video_files, time_tolerance=5):
    """Groups videos into trials allowing a ±time_tolerance seconds difference."""
    trials = []
    
    # Extract timestamps and sort videos by timestamp
    video_data = [(file, parse_timestamp(file)) for file in video_files]
    video_data = [v for v in video_data if v[1] is not None]  # Remove invalid timestamps
    video_data.sort(key=lambda x: x[1])  # Sort by timestamp
    
    # Group videos into trials
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


if __name__ == "__main__":
    video_folder = "C:\\videos\\DCIM\\1"
    video_files = [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith(".MP4")]

    print("🔍 Found video files:")
    for v in video_files:
        print(f"   - {v}")

    trials = group_videos_by_trial(video_files)

    all_results = {}
    for trial in trials:
        # Get the trial name from the timestamp of the first video in the trial
        trial_name = parse_timestamp(trial[0][0]).strftime("%Y%m%d_%H%M%S")
        print(f"\n🚀 Processing trial: {trial_name}")
        video_list = [video[0] for video in trial]  # Extraire uniquement les noms de fichiers
        results = synchronize_videos(trial_name, video_list)
        if results:
            all_results[trial_name] = results

    json_file_path = "output.json"
    with open(json_file_path, "w") as json_file:
        json.dump(all_results, json_file, indent=4)
    
    print(f"📂 Data saved to {json_file_path}")
