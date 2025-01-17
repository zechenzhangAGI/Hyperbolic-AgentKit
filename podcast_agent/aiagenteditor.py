import os
import vertexai
import pathlib
import time
from google.api_core.exceptions import ResourceExhausted
from langchain.output_parsers import StructuredOutputParser
from langchain.output_parsers.structured import ResponseSchema
import json
import subprocess

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/amr/Hyperbolic-AgentKit/eaccservicekey.json"
PROJECT_ID = "evolution-acceleration"
LOCATION = "us-central1"

MAX_RETRIES = 3
INITIAL_BACKOFF = 1

vertexai.init(project=PROJECT_ID, location=LOCATION)

from vertexai.generative_models import (
    GenerativeModel,
    Part,
)

MODEL_ID = "gemini-1.5-pro"
model = GenerativeModel(MODEL_ID)

def trim_video(input_path, output_path, start_time, end_time):
    """Trim video using ffmpeg"""
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', start_time,
        '-to', end_time,
        '-c', 'copy',
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return False

def concatenate_videos(clip_paths, output_path):
    """Concatenate multiple video clips into one final video"""
    # Create a temporary file listing all clips
    list_file = "temp_list.txt"
    try:
        with open(list_file, "w") as f:
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")
        
        # Use ffmpeg to concatenate the clips
        command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        os.remove(list_file)  # Clean up temp file
        return True
    except Exception as e:
        print(f"Error concatenating videos: {str(e)}")
        if os.path.exists(list_file):
            os.remove(list_file)  # Clean up temp file if it exists
        return False

# Debug: Print file info
videopath = "/Users/amr/Hyperbolic-AgentKit/audiofiles/Akshatpt2first.mov"
print(f"Attempting to process video: {videopath}")
print(f"File exists: {os.path.exists(videopath)}")
if os.path.exists(videopath):
    print(f"File size: {os.path.getsize(videopath)} bytes")

try:
    video_bytes = pathlib.Path(videopath).read_bytes()
    print(f"Successfully read video bytes. Size: {len(video_bytes)}")
    video_file = Part.from_data(video_bytes, mime_type="video/mov")
    print("Successfully created Part object")
except Exception as e:
    print(f"Error reading video file: {str(e)}")
    raise

prompt = """Please watch this video carefully and analyze it for potential edits.
I need specific timestamps for parts we should keep or remove.

Analyze the content and provide editing suggestions in this exact JSON format:
{
    "edits": [
        {
            "start_time": "HH:MM:SS",
            "end_time": "HH:MM:SS",
            "keep": true,
            "reason": "Explain why this segment should be kept or removed"
        }
    ]
}

Focus on identifying:
1. Key discussion points to keep
2. Any technical issues or dead air to remove
3. Sections that might need trimming for pacing
"""

print("\nSending request to Gemini...")
print(f"Prompt length: {len(prompt)} characters")

contents = [video_file, prompt]

for attempt in range(MAX_RETRIES):
    try:
        print(f"Attempt {attempt + 1} of {MAX_RETRIES}")
        responses = model.generate_content(contents)
        print("\nReceived response from Gemini:")
        print("Response type:", type(responses))
        print("Raw response:", responses.text)
        break
    except ResourceExhausted as e:
        if attempt == MAX_RETRIES - 1:
            sleep_time = INITIAL_BACKOFF * (2 ** attempt)
            print(f"Rate limit hit. Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            raise
    except Exception as e:
        print(f"Unexpected error during generate_content: {str(e)}")
        raise

try:
    cleaned_response = responses.text.strip()
    print("\nCleaned response:", cleaned_response[:200] + "..." if len(cleaned_response) > 200 else cleaned_response)
    
    if cleaned_response.startswith('```json'):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.endswith('```'):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()
    
    print("\nAttempting to parse JSON...")
    json_data = json.loads(cleaned_response)
    print("Successfully parsed JSON")
    
    # Create output directory
    output_dir = "edited_clips"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nCreated output directory: {output_dir}")
    
    # Keep track of successful clips for concatenation
    successful_clips = []
    
    # Process edits
    if "edits" in json_data:
        for i, edit in enumerate(json_data["edits"]):
            if edit["keep"]:
                output_path = os.path.join(
                    output_dir,
                    f"clip_{i}_{os.path.basename(videopath)}"
                )
                print(f"\nProcessing clip {i+1}...")
                print(f"Start time: {edit['start_time']}")
                print(f"End time: {edit['end_time']}")
                print(f"Reason: {edit['reason']}")
                
                success = trim_video(
                    videopath,
                    output_path,
                    edit["start_time"],
                    edit["end_time"]
                )
                
                if success:
                    print(f"Successfully created clip {i+1}")
                    successful_clips.append(output_path)
                else:
                    print(f"Failed to create clip {i+1}")
    else:
        print("\nNo 'edits' key found in JSON response")
        print("Full JSON data:", json_data)
    
    # Concatenate all successful clips into final video
    if successful_clips:
        final_output = os.path.join(output_dir, f"final_edited_{os.path.basename(videopath)}")
        print("\nConcatenating clips into final video...")
        if concatenate_videos(successful_clips, final_output):
            print(f"Successfully created final edited video: {final_output}")
        else:
            print("Failed to create final edited video")
    
    # Save analysis
    output_filename = os.path.splitext(os.path.basename(videopath))[0] + "_edits.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved editing suggestions to: {output_path}")
    
except json.JSONDecodeError as e:
    print(f"\nError decoding JSON: {str(e)}")
    print("Response content:")
    print(responses.text)
except Exception as e:
    print(f"\nUnexpected error: {str(e)}")
    print(f"Error type: {type(e)}")
    if hasattr(e, '__traceback__'):
        import traceback
        print("Traceback:")
        traceback.print_tb(e.__traceback__)

print("\nScript completed.")