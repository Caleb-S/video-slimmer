import argparse
import time
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import speedx

# Define constants
TARGET_FPS = 24
VIDEO_BITRATE = '1000k'
MAX_WIDTH = 1280
MAX_HEIGHT = 720

def reduce_fps(input_file, output_file):
    start_time = time.time()

    # Load the input video
    video_clip = VideoFileClip(input_file)

    # Check the original FPS and dimensions
    original_fps = video_clip.fps
    original_width, original_height = video_clip.size

    if original_fps <= 0:
        print(f"Error: Invalid original FPS ({original_fps}) for the video.")
        return

    # Ensure TARGET_FPS is less than original_fps to avoid ZeroDivisionError
    if TARGET_FPS >= original_fps:
        print(f"Warning: Target FPS ({TARGET_FPS}) is greater than or equal to original FPS ({original_fps}). No frames will be written.")
        target_fps = original_fps
    else:
        target_fps = TARGET_FPS  # Set to the constant value

    # Resize the video if it exceeds 720p
    if original_width > MAX_WIDTH or original_height > MAX_HEIGHT:
        video_clip = video_clip.resize(height=MAX_HEIGHT)  # Resize while maintaining aspect ratio

    # Set the new FPS
    video_clip = video_clip.set_fps(target_fps)
    #video_clip = speedx(video_clip, factor=1.25)

    # Write the final output file with audio
    video_clip.write_videofile(
        output_file,
        codec='libx264',          # Set the codec for the output file
        audio_codec='aac',        # Set audio codec
        audio_bitrate='96k',      # Set audio bitrate
        bitrate=VIDEO_BITRATE,      # Set video bitrate
        preset='ultrafast'
    )

    # Close the video clip
    video_clip.close()

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken to create the video: {total_time:.2f} seconds")

def update_all_videos():
    # Get all video files in the current directory
    video_files = sorted(list(filter(lambda x: x.endswith('.mp4'), os.listdir('.'))))

    for video_file in video_files:
        input_file = os.path.join(os.getcwd(), video_file)
        output_file = os.path.join(os.getcwd(), video_file)
        reduce_fps(input_file, output_file)

    print("All videos have been updated.")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Reduce the FPS of a video.")
    parser.add_argument('input_file', type=str, help="The path to the input video file.")
    parser.add_argument('output_file', type=str, help="The path to the output video file.")
    parser.add_argument('-flag_1', type=str, help="flag",  default='')
    args = parser.parse_args()

    if args.flag_1 == "-all":
        update_all_videos()
    else:
        reduce_fps(args.input_file, args.output_file)



