import cv2
import argparse
from moviepy.editor import VideoFileClip

def reduce_fps(input_file, output_file, target_fps):
    # Open the input video
    cap = cv2.VideoCapture(input_file)
    
    # Check if the video was opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_file}.")
        return

    # Get the original width, height, and FPS
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    original_audio = cap.get(cv2.CAP_PROP_POS_AVI_RATIO)

    # Check if the original FPS is valid
    if original_fps <= 0:
        print(f"Error: Invalid original FPS ({original_fps}) for the video.")
        cap.release()
        return


    # Ensure target_fps is less than original_fps to avoid ZeroDivisionError
    if target_fps >= original_fps:
        print(f"Warning: Target FPS ({target_fps}) is greater than or equal to original FPS ({original_fps}). No frames will be written.")
        cap.release()
        return

    # Define the codec and create a VideoWriter object to write the new video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for .mp4 files
    out = cv2.VideoWriter('temp_video.mp4', fourcc, target_fps, (width, height))

    frame_interval = int(original_fps // target_fps)  # Skip frames to reduce FPS

    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Write only every nth frame to achieve target FPS
        if count % frame_interval == 0:
            out.write(frame)
        
        count += 1
    
    cap.release()
    out.release()

    # Use MoviePy to combine the audio with the newly created video
    video_clip = VideoFileClip('temp_video.mp4')
    audio_clip = VideoFileClip(input_file).audio


    # Set the audio of the new video to the original audio
    video_with_audio = video_clip.set_audio(audio_clip)


    # Write the final output file with audio
    # Other bitrates: 320k, 256k(good for music), 192k(acceptable), 128k(good for speech) 
    video_with_audio.write_videofile(output_file, audio_codec='aac', audio_bitrate='128k')

    #discard temp video
    os.remove('temp_video.mp4')

    video_clip.close()
    audio_clip.close()

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Reduce the FPS of a video.")
    parser.add_argument('input_file', type=str, help="The path to the input video file.")
    parser.add_argument('output_file', type=str, help="The path to the output video file.")
    parser.add_argument('fps', type=int, help="The target FPS for the output video.")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the function with arguments from the CLI
    reduce_fps(args.input_file, args.output_file, args.fps)

