import os
import vertexai
import pathlib
import time
from google.api_core.exceptions import ResourceExhausted
from langchain.output_parsers import StructuredOutputParser
from langchain.output_parsers.structured import ResponseSchema
import json
import os

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

def get_speaker_description(image_path, speaker_name):
    image_bytes = pathlib.Path(image_path).read_bytes()
    image_part = Part.from_data(image_bytes, mime_type="image/png")
    
    description_prompt = f"Please describe what {speaker_name} looks like in this image, focusing on distinguishing features that would help identify when they are speaking in a video."
    
    response = model.generate_content([image_part, description_prompt])
    return response.text.strip()

def process_video_file(videopath):
    video_bytes = pathlib.Path(videopath).read_bytes()
    video_file = Part.from_data(video_bytes, mime_type="video/mov")

    prompt = f"""
    The name of this podcast is The Rollup. There are two hosts in this interview:
    - Andy: Has light blonde, curly hair. His hair is longer on top and styled with a bit of wave. He has a light complexion.
    - Rob: Has short, dark hair with a slightly receding hairline. He has a light to medium skin tone and a short beard that follows his jawline. 

    Any other speakers in this interview are guests, and they should be identified as such.

    Please completely transcribe this interview in its entirety, identify the speakers based on these descriptions, and return the transcript in precisely the following JSON format:
    """
    
    prompt += """
    [
      {
        "speaker": "Speaker Name",
        "content": "What they said"
      },
      {
        "speaker": "Speaker Name",
        "content": "What they said"
      },
      {
        "speaker": "Speaker Name",
        "content": "What they said"
      }
    ]
    """

    contents = [video_file, prompt]
    
    for attempt in range(MAX_RETRIES):
        try:
            responses = model.generate_content(contents)
            break
        except ResourceExhausted as e:
            if attempt == MAX_RETRIES - 1:
                sleep_time = INITIAL_BACKOFF * (2 ** attempt)
                print(f"Rate limit hit. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise

    try:
        print(f"\n=== Processing {os.path.basename(videopath)} ===")
        print("\n=== Starting JSON Processing ===")
        
        print("1. Cleaning response text...")
        cleaned_response = responses.text.strip()
        if cleaned_response.startswith('```json'):
            print("- Removing leading ```json")
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            print("- Removing trailing ```")
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        print("Cleaned response length:", len(cleaned_response))
        print("First 100 chars:", cleaned_response[:100])
        
        print("\n2. Parsing JSON...")
        json_data = json.loads(cleaned_response)
        print(f"Successfully parsed JSON with {len(json_data)} entries")
        
        print("\n3. Setting up output schema...")
        response_schemas = [
            ResponseSchema(name="speaker", description="The name of the speaker"),
            ResponseSchema(name="content", description="The content of the speech")
        ]
        parser = StructuredOutputParser(response_schemas=response_schemas)
        
        print("\n4. Creating output directory...")
        os.makedirs("jsonoutputs", exist_ok=True)
        
        print("\n5. Preparing file path...")
        output_filename = os.path.splitext(os.path.basename(videopath))[0] + ".json"
        output_path = os.path.join("jsonoutputs", output_filename)
        print(f"Output path: {output_path}")
        
        print("\n6. Writing JSON to file...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Successfully wrote transcript to {output_path}")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Error decoding JSON from response: {str(e)}")
        print("\nResponse content:")
        print("=" * 50)
        print(responses.text)
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Error processing {os.path.basename(videopath)}: {str(e)}")

    print("\nOriginal response:")
    print("=" * 50)
    print(responses.text)
    print("=" * 50)

def main():
    # Get descriptions for each speaker (commented out as in original)
    # andy_desc = get_speaker_description("/Users/amr/Hyperbolic-AgentKit/speaker_images/Andy.png", "Andy")
    # rob_desc = get_speaker_description("/Users/amr/Hyperbolic-AgentKit/speaker_images/Rob.png", "Rob")
    # weidai_desc = get_speaker_description("/Users/amr/Hyperbolic-AgentKit/speaker_images/weidai.png", "Wei Dai")

    # Process all video files in the directory
    audio_files_dir = "/Users/amr/Hyperbolic-AgentKit/audiofiles"
    supported_extensions = ('.mov', '.mp4', '.avi')  # Add more video formats as needed

    for filename in os.listdir(audio_files_dir):
        if filename.lower().endswith(supported_extensions):
            videopath = os.path.join(audio_files_dir, filename)
            print(f"\n📽️ Processing video: {filename}")
            process_video_file(videopath)

if __name__ == "__main__":
    main()

