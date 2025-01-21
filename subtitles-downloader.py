import os
import argparse
import babelfish
import sys
from subliminal import download_best_subtitles, region, save_subtitles
from subliminal.video import Video
from babelfish import Language

def find_video_files(root_folder, extensions=(".mp4", ".mkv", ".avi", ".mov")):
    """Recursively find all video files in the root folder with the given extensions."""
    video_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith(extensions):
                video_files.append(os.path.join(dirpath, filename))
    return video_files

def has_subtitle(video_path):
    """Check if a subtitle file exists for the given video file."""
    video_dir, video_name = os.path.split(video_path)
    video_base, _ = os.path.splitext(video_name)
    for file in os.listdir(video_dir):
        if file.startswith(video_base) and file.endswith(('.srt', '.sub', '.ass', '.vtt')):
            return True
    return False

def download_subtitles_for_videos(video_files, language_code):
    """Download subtitles for a list of video files in the given language."""
    # Initialize subliminal region
    region.configure('dogpile.cache.memory')

    # Convert language code to subliminal's Language
    language = Language(language_code)

    for video_path in video_files:
        if has_subtitle(video_path):
            print(f"Skipping {video_path}: Subtitle already exists.")
            continue

        print(f"Processing: {os.path.basename(video_path)} ({video_path})")
        try:
            # Create a Video object
            video = Video.fromname(video_path)

            # Download the best subtitles for the video
            subtitles = download_best_subtitles([video], {language})

            if subtitles.get(video):
                # Save the subtitles to the video directory
                save_subtitles(video, subtitles[video])
                print(f"Subtitles downloaded and saved for: {video_path}")
            else:
                print(f"No subtitles found for: {video_path}")

        except Exception as e:
            print(f"Error processing {video_path}: {e}")

def main():
    if len(sys.argv) == 1:
        print("Available languages:")
        for code in babelfish.language.LANGUAGES:
            print(f"  {code}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Download subtitles for video files in a specified folder.")
    parser.add_argument("--folder", type=str, help="Path to the root folder containing video files.", required=True)
    parser.add_argument("--lang", type=str, help="Subtitle language code (e.g., 'en' for English).", required=True)
    args = parser.parse_args()

    # Find all video files in the root folder
    print("Searching for video files...")
    video_files = find_video_files(args.folder)

    if not video_files:
        print("No video files found in the specified folder.")
        return

    # Download subtitles for the found video files
    print("Downloading subtitles...")
    download_subtitles_for_videos(video_files, args.lang)

if __name__ == "__main__":
    main()