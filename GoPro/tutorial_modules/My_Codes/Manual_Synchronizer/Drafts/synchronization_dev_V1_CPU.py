import cv2
import os
import keyboard
from tqdm import tqdm

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


def update_frame(val):
    """Callback function to update the frame when the trackbar is moved."""
    global frame_number, video, window_name
    frame_number = val  # Update the global frame number

    # Update the displayed frame immediately
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    if ret:
        display_frame = cv2.resize(frame, (640, 480))
        cv2.putText(display_frame, f"Frame: {frame_number}/{total_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow(window_name, display_frame)

def navigate_frames(video_capture, win_name="Select Reference Frame"):
    global frame_number, total_frames, video, window_name

    if video_capture is None:
        print("❌ Error: Video is not loaded correctly.")
        return None

    video = video_capture  # Store video globally for trackbar callback
    window_name = win_name  # Store window name
    frame_number = 0  # Start at the first frame
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        print("❌ Error: Video has no frames.")
        return None

    cv2.namedWindow(window_name)
    cv2.createTrackbar("Frame", window_name, 0, total_frames - 1, update_frame)

    while True:
        # Set video to the current frame
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = video.read()
        if not ret:
            break

        # Resize for display and add text overlay
        display_frame = cv2.resize(frame, (640, 480))
        cv2.putText(display_frame, f"Frame: {frame_number}/{total_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):  # Quit
            break
        elif key == ord('s'):  # Select reference frame
            print(f"✅ Reference frame selected: {frame_number}")
            return frame_number
        elif key == ord('d'):  # Move forward
            frame_number = min(frame_number + 1, total_frames - 1)
        elif key == ord('a'):  # Move backward
            frame_number = max(0, frame_number - 1)

        # Update the trackbar position
        cv2.setTrackbarPos("Frame", window_name, frame_number)

    cv2.destroyAllWindows()
    return frame_number
    
    return frame_number
def synchronize_videos(video_paths, output_folder):
    if not video_paths:
        print("❌ Error: No video files found in the directory.")
        return
    
    reference_path, _ = find_reference_video(video_paths)
    if reference_path is None:
        print("❌ Error: No valid reference video found.")
        return
    
    reference_video = open_video(reference_path)
    if reference_video is None:
        return
    
    reference_frame = navigate_frames(reference_video, "Reference Video")
    reference_video.release()
    if reference_frame is None:
        return
    
    offsets = {}
    for video_path in video_paths:
        video = open_video(video_path)
        if video:
            offset = navigate_frames(video, f"Sync {os.path.basename(video_path)}")
            if offset is not None:
                offsets[video_path] = offset - reference_frame
            video.release()
    
    print("\n✅ Synchronization completed with offsets:")
    for vid, off in offsets.items():
        print(f"{vid}: {off} frames")

if __name__ == "__main__":
    video_folder = "C:\\videos\\DCIM\\1"
    video_files = [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith(".MP4")]
    print("🔍 Found video files:")
    for v in video_files:
        print(f"   - {v}")
    synchronize_videos(video_files, video_folder)