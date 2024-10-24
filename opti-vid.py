import argparse
import time
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import speedx
import os
import subprocess
import json

# Define constants
TARGET_FPS = 24
VIDEO_BITRATE = '350k'
MAX_WIDTH = 1280
MAX_HEIGHT = 720

# Todo:
# only change bitrate, fpx or resolution if greater than target values
# if all values are less than target values, don't change anything
# place file back in original folder
def round_bitrate(bitrate):
    """Round the given bitrate to the nearest thousand and convert to kilobits."""
    if bitrate is None:
        return None  # Handle None case gracefully

    # Round to the nearest thousand
    rounded = round(bitrate / 1000)  # Divide by 1000 and round
    return rounded  #

def get_bitrate(file_path):
    # Run ffprobe to get video/audio information
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'stream=index,bit_rate',
        '-of', 'json',
        file_path
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Print error output for debugging
    if result.stderr:
        print(f"Error while running ffprobe: {result.stderr}")

    try:
        info = json.loads(result.stdout)
        # Check if 'streams' key exists
        video_bitrate = int(info['streams'][0]['bit_rate']) if len(info['streams']) > 0 and 'bit_rate' in info['streams'][0] else None
        audio_bitrate = int(info['streams'][1]['bit_rate']) if len(info['streams']) > 1 and 'bit_rate' in info['streams'][1] else None

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None, None

    rounded_bitrate1 = round_bitrate(video_bitrate)
    rounded_bitrate2 = round_bitrate(audio_bitrate)

    return rounded_bitrate1, rounded_bitrate2


def reduce_fps(input_file, output_file):
    # Define constants
    TARGET_FPS = 24
    VIDEO_BITRATE = '350k'
    MAX_WIDTH = 1280
    MAX_HEIGHT = 720
    audio_bitrate = 64
    audio_fps = 32000

    num_cores = os.cpu_count()
    print(VIDEO_BITRATE)

    # Load the input video
    video_clip = VideoFileClip(input_file)

    # Check the original FPS and dimensions
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
        target_fps = TARGET_FPS  # Set to the constant value
        video_clip = video_clip.set_fps(target_fps)

    if original_width > MAX_WIDTH or original_height > MAX_HEIGHT:
        video_clip = video_clip.resize(height=MAX_HEIGHT)  # Resize while maintaining aspect ratio

    # Write the final output file with audio
    video_clip.write_videofile(
        output_file,
        codec='libx264',          # Set the codec for the output file
        audio_codec='aac',        # Set audio codec
        audio_bitrate='64k',      # Set audio bitrate
        audio_fps=original_audio_fps,
        bitrate=VIDEO_BITRATE,      # Set video bitrate
        preset='ultrafast',       # Set video encoding preset
        threads=num_cores
    )

    # Close the video clip
    video_clip.close()

def update_all_videos():

    start_time = time.time()
    # Recursively find all video files and process them
    for root, dirs, files in os.walk("."):  # Recursively search current directory
        for file in files:
            if file.endswith((".mp4")):  # Add more extensions as needed
                input_file = os.path.join(root, file)
                output_file = os.path.join(root, f"TEMP_{file}")
                input_file = os.path.abspath(input_file)
                #get full file path from hard drive
                try: 
                    reduce_fps(input_file, output_file)
                    if os.path.exists(input_file):
                        os.remove(input_file)
                    os.rename(output_file, input_file)
                except Exception as e:
                    print(f"Error processing {input_file}: {e}")

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken to create the video: {total_time:.2f} seconds")
if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Reduce the FPS of a video.")
    
    # Optional -a or --all flag to target all videos
    parser.add_argument('-a', '--all', action='store_true', help="Process all videos recursively.")
    
    # Positional arguments for input and output files (optional when -a is used)
    parser.add_argument('input_file', type=str, nargs='?', help="The path to the input video file.")
    parser.add_argument('output_file', type=str, nargs='?', help="The path to the output video file.")
    
    args = parser.parse_args()

    # Logic to handle either recursive processing or single video processing
    if args.all:
        update_all_videos()
    elif args.input_file and args.output_file:
        reduce_fps(args.input_file, args.output_file)
    else:
        print("Error: You must provide either input and output files, or use the '-a' flag to process all videos.")

