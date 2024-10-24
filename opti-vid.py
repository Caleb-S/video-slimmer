import argparse
import time
from moviepy.editor import VideoFileClip
import os
import subprocess
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import random

# Define constants
TARGET_FPS = 24
VIDEO_BITRATE = '350k'
MAX_WIDTH = 1280
MAX_HEIGHT = 720

def round_bitrate(bitrate):
    """Round the given bitrate to the nearest thousand and convert to kilobits."""
    if bitrate is None:
        return None
    rounded = round(bitrate / 1000)
    return rounded

def get_bitrate(file_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'stream=index,bit_rate',
        '-of', 'json',
        file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stderr:
        print(f"Error while running ffprobe: {result.stderr}")

    try:
        info = json.loads(result.stdout)
        video_bitrate = int(info['streams'][0]['bit_rate']) if len(info['streams']) > 0 and 'bit_rate' in info['streams'][0] else None
        audio_bitrate = int(info['streams'][1]['bit_rate']) if len(info['streams']) > 1 and 'bit_rate' in info['streams'][1] else None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None, None

    rounded_bitrate1 = round_bitrate(video_bitrate)
    rounded_bitrate2 = round_bitrate(audio_bitrate)

    return rounded_bitrate1, rounded_bitrate2

def reduce_fps(input_file, output_file):
    TARGET_FPS = 24
    VIDEO_BITRATE = '350k'
    MAX_WIDTH = 1280
    MAX_HEIGHT = 720
    audio_bitrate = 64
    audio_fps = 32000

    num_cores = os.cpu_count()
    video_clip = VideoFileClip(input_file)

    original_fps = video_clip.fps
    original_width, original_height = video_clip.size
    original_video_bitrate, original_audio_bitrate = get_bitrate(input_file)
    original_audio_fps = video_clip.audio.fps

    if original_height < MAX_HEIGHT and original_width < MAX_WIDTH and original_fps < TARGET_FPS and original_audio_fps < 32000 and original_audio_bitrate < 64 and original_video_bitrate < 350:
        return

    if original_audio_fps < audio_fps:
        audio_fps = None
    if original_audio_bitrate < audio_bitrate:
        audio_bitrate = None
    else:
        audio_bitrate = f"{original_audio_bitrate}k"

    if TARGET_FPS < original_fps:
        video_clip = video_clip.set_fps(TARGET_FPS)
    if original_width > MAX_WIDTH or original_height > MAX_HEIGHT:
        video_clip = video_clip.resize(height=MAX_HEIGHT)

    video_clip.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='64k',
        audio_fps=original_audio_fps,
        bitrate=VIDEO_BITRATE,
        preset='ultrafast',
        threads=num_cores,
        logger=None
    )
    video_clip.close()

def process_video(input_file):
    random_number = random.randint(1000, 9999)
    
    # Create a unique output file path by appending the random number
    output_file = os.path.join(os.path.dirname(input_file), f"TEMP_{random_number}_{os.path.basename(input_file)}")

    try:
        reduce_fps(input_file, output_file)
        if os.path.exists(input_file):
            os.remove(input_file)
        os.rename(output_file, input_file)
    except Exception as e:
        print(f"Error processing {input_file}: {e}")

def update_all_videos_concurrently():
    start_time = time.time()
    video_files = []
    num_workers = os.cpu_count() // 2 if os.cpu_count() is not None else 1
    
    # Collect all video files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".mp4"):
                video_files.append(os.path.abspath(os.path.join(root, file)))

    # Initialize progress bar with total number of videos
    total_videos = len(video_files)
    with tqdm(total=total_videos, desc="Processing Videos", unit="video") as progress_bar:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_video, file) for file in video_files]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in processing: {e}")
                progress_bar.update(1)  # Update progress for each completed video

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken to process videos: {total_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reduce the FPS of a video.")
    parser.add_argument('-a', '--all', action='store_true', help="Process all videos recursively.")
    parser.add_argument('input_file', type=str, nargs='?', help="The path to the input video file.")
    parser.add_argument('output_file', type=str, nargs='?', help="The path to the output video file.")
    args = parser.parse_args()

    if args.all:
        update_all_videos_concurrently()
    elif args.input_file and args.output_file:
        process_video(args.input_file)
    else:
        print("Error: You must provide either input and output files, or use the '-a' flag to process all videos.")

