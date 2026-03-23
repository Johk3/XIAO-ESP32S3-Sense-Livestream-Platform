import os
import sys
import time
import json
import glob
import subprocess
import re
import psutil
from dotenv import load_dotenv

load_dotenv()

# ================= CONFIGURATION =================
# Set this to where you want the videos to permanently live
OUTPUT_DIR = os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Documents/Camera_Videos"))
# The framerate you want the reconstruct videos to be at
FPS = int(os.getenv("FPS", "10"))
# =================================================

STATE_FILE = os.path.join(OUTPUT_DIR, ".processed_frames.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_state(state):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(list(state), f)

def get_usb_drives():
    drives = []
    for partition in psutil.disk_partitions():
        # Common USB mount points / removable drives
        if 'loop' not in partition.device and (
            '/media/' in partition.mountpoint or 
            '/run/media/' in partition.mountpoint or 
            '/Volumes/' in partition.mountpoint or
            os.name == 'nt'  # Windows usually maps all physical drives
        ):
            drives.append(partition.mountpoint)
    return drives

def is_camera_drive(mountpoint):
    try:
        # Quick check if it has a YYYY structured folder inside
        for item in os.listdir(mountpoint):
            if re.match(r'^20\d{2}$', item) and os.path.isdir(os.path.join(mountpoint, item)):
                return True
    except PermissionError:
        pass
    return False

def find_new_frames(mountpoint, processed_frames):
    new_frames_by_hour = {}
    
    # Structure is /YYYY/MM/DD/HH/YYYYMMDD_HHMMSSxxx.jpg
    pattern = os.path.join(mountpoint, '20[0-9][0-9]', '[0-1][0-9]', '[0-3][0-9]', '[0-2][0-9]', '*.jpg')
    all_jpegs = glob.glob(pattern)
    
    for jpg in all_jpegs:
        filename = os.path.basename(jpg)
        if filename not in processed_frames:
            # Group by its actual containing hour folder path cleanly mapping the structure
            rel_path = os.path.relpath(os.path.dirname(jpg), mountpoint)
            if rel_path not in new_frames_by_hour:
                new_frames_by_hour[rel_path] = []
            new_frames_by_hour[rel_path].append(jpg)
            
    # Chronological sort directly on paths since the timestamp is in the name properly
    for hour in new_frames_by_hour:
        new_frames_by_hour[hour].sort()
        
    return new_frames_by_hour

def compile_video(rel_path, frames, processed_frames):
    if not frames:
        return
        
    out_dir = os.path.join(OUTPUT_DIR, rel_path)
    os.makedirs(out_dir, exist_ok=True)
    
    # Video Name: firstframe_to_lastframe.mp4
    first_frame = os.path.basename(frames[0]).replace('.jpg', '')
    last_frame = os.path.basename(frames[-1]).replace('.jpg', '')
    out_file = os.path.join(out_dir, f"{first_frame}_to_{last_frame}.mp4")
    
    print(f"[{time.strftime('%H:%M:%S')}] Compiling {len(frames)} new frames into: {out_file}")
    
    list_file_path = os.path.join(out_dir, "ffmpeg_list.txt")
    with open(list_file_path, "w") as f:
        for frame in frames:
            # Safe quoting just in case
            safe_frame_path = frame.replace("'", "'\\''") 
            f.write(f"file '{safe_frame_path}'\n")
            f.write(f"duration {1.0/FPS}\n")
        # FFmpeg concat demuxer quirk: Last frame duration is sometimes dropped unless we explicitly add a dummy frame
        f.write(f"file '{safe_frame_path}'\n")
    
    # FFmpeg concat command
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
        "-i", list_file_path, 
        "-c:v", "libx264", "-pix_fmt", "yuv420p", 
        out_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Successfully created -> {out_file}")
        
        for frame in frames:
            processed_frames.add(os.path.basename(frame))
        save_state(processed_frames)
        
    except subprocess.CalledProcessError as e:
        print(f"Error compiling video for {rel_path}")
    except FileNotFoundError:
        print("CRITICAL ERROR: ffmpeg is not installed or not in PATH. Please install ffmpeg.")
        sys.exit(1)
    finally:
        if os.path.exists(list_file_path):
            os.remove(list_file_path)

def main():
    print("="*60)
    print(f"🚀 Auto Video Converter Started")
    print(f"📂 Output Directory: {OUTPUT_DIR}")
    print(f"⏳ Waiting for USB drive insertions...")
    print("="*60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    processed_frames = load_state()
    
    try:
        while True:
            drives = get_usb_drives()
            for drive in drives:
                if is_camera_drive(drive):
                    frames_by_hour = find_new_frames(drive, processed_frames)
                    if frames_by_hour:
                        print(f"\n[{time.strftime('%H:%M:%S')}] Detected camera drive with new frames at: {drive}")
                        for rel_path, frames in frames_by_hour.items():
                            compile_video(rel_path, frames, processed_frames)
                        print(f"[{time.strftime('%H:%M:%S')}] All new frames processed!")
                        print("⏳ Resuming wait for new frames...")
                        
            time.sleep(5)  # Poll comfortably every 5 seconds
            
    except KeyboardInterrupt:
        print("\n[!] Exiting automatically as requested. Bye!")

if __name__ == "__main__":
    main()
