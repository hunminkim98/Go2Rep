import cv2
import os
import numpy as np
import keyboard
from tqdm import tqdm
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule

##to run the code
##Conda activate cudatest 
##"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
##where cl
##nvcc --version
##spyder


# Initialize CUDA kernel
kernel_code = """
__global__ void process_frame(unsigned char *frame, int width, int height) {
    int x = threadIdx.x + blockIdx.x * blockDim.x;
    int y = threadIdx.y + blockIdx.y * blockDim.y;
    if (x < width && y < height) {
        int idx = (y * width + x) * 3;  // Assuming 3-channel (RGB) image
        frame[idx] = 255 - frame[idx];  // Invert colors (example processing)
    }
}
"""

mod = SourceModule(kernel_code)
process_frame = mod.get_function("process_frame")



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

frame_cache = {}  # Global dictionary to cache frames

def get_frame(video, frame_number):
    if frame_number in frame_cache:
        return frame_cache[frame_number]
    
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    if ret:
        frame_cache[frame_number] = frame
    return frame

def navigate_frames(video_capture, win_name="Select Reference Frame"):
    global frame_number, total_frames, video, window_name
    frame_cache.clear()  # Clear cached frames when a new video starts
    if video_capture is None:
        print("❌ Error: Video is not loaded correctly.")
        return None

    video = video_capture
    window_name = win_name
    frame_number = 0
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        print("❌ Error: Video has no frames.")
        return None

    while True:
        frame = get_frame(video, frame_number)
        if frame is None:
            break

        # Send frame to GPU memory
        frame_gpu = cuda.mem_alloc(frame.nbytes)
        cuda.memcpy_htod(frame_gpu, frame)

        # Call CUDA kernel to process the frame
        process_frame(
            frame_gpu,
            np.int32(frame.shape[1]),
            np.int32(frame.shape[0]),
            block=(32, 32, 1),
            grid=(frame.shape[1] // 32 + 1, frame.shape[0] // 32 + 1)
        )

        # Get processed frame back from GPU
        cuda.memcpy_dtoh(frame, frame_gpu)

        # Resize for display
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
            frame_number = min(frame_number + 1, total_frames - 1)
        elif key == ord('a'):
            frame_number = max(0, frame_number - 1)
        elif key == ord('n'):  # New functionality for N key
            try:
                user_input = int(input(f"Enter the frame number (0 - {total_frames - 1}): "))
                if 0 <= user_input < total_frames:
                    frame_number = user_input
                else:
                    print(f"❌ Invalid frame number. Please enter a value between 0 and {total_frames - 1}.")
            except ValueError:
                print("❌ Invalid input. Please enter a valid integer.")
    cv2.destroyAllWindows()  # Close all windows
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

    cv2.destroyAllWindows()  # Close all windows after synchronization is completed
    
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
