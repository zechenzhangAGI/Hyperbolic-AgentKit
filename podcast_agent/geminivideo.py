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

# First, get descriptions of each speaker
def get_speaker_description(image_path, speaker_name):
    image_bytes = pathlib.Path(image_path).read_bytes()
    image_part = Part.from_data(image_bytes, mime_type="image/png")
    
    description_prompt = f"Please describe what {speaker_name} looks like in this image, focusing on distinguishing features that would help identify when they are speaking in a video."
    
    response = model.generate_content([image_part, description_prompt])
    return response.text.strip()

# Get descriptions for each speaker
andy_desc = get_speaker_description("/Users/amr/Hyperbolic-AgentKit/speaker_images/Andy.png", "Andy")
rob_desc = get_speaker_description("/Users/amr/Hyperbolic-AgentKit/speaker_images/Rob.png", "Rob")
weidai_desc = get_speaker_description("/Users/amr/Hyperbolic-AgentKit/speaker_images/weidai.png", "Wei Dai")

# Use these descriptions in the main video processing
videopath = "/Users/amr/Hyperbolic-AgentKit/audiofiles/InfratoAppspt1.mp4"
video_bytes = pathlib.Path(videopath).read_bytes()
video_file = Part.from_data(video_bytes, mime_type="video/mp4")

prompt = f"""
There are three speakers in this interview. Here are their descriptions based on their appearance:
Andy: {andy_desc}
Rob: {rob_desc}
Wei Dai: {weidai_desc}

Please completely transcribe this interview in its entirety, identify the speakers based on these descriptions, and return the transcript in precisely the following JSON format:
"""
print(andy_desc)
print(rob_desc)
print(weidai_desc)
# Add the JSON format example as a separate raw string
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
    cleaned_response = responses.text.strip()
    if cleaned_response.startswith('```json'):
        cleaned_response = cleaned_response[7:]  # Remove ```json
    if cleaned_response.endswith('```'):
        cleaned_response = cleaned_response[:-3]  # Remove closing ```
    cleaned_response = cleaned_response.strip()  # Remove any remaining whitespace
    
    json_data = json.loads(cleaned_response)
    
    response_schemas = [
        ResponseSchema(name="speaker", description="The name of the speaker"),
        ResponseSchema(name="content", description="The content of the speech")
    ]
    
    parser = StructuredOutputParser(response_schemas=response_schemas)
    
    os.makedirs("jsonoutputs", exist_ok=True)
    
    output_filename = os.path.splitext(os.path.basename(videopath))[0] + ".json"
    output_path = os.path.join("jsonoutputs", output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully wrote transcript to {output_path}")
    
except json.JSONDecodeError as e:
    print(f"Error decoding JSON from response: {str(e)}")
    print("Response content:")
    print(responses.text) 
except Exception as e:
    print(f"Error processing or writing JSON: {str(e)}")

print("Original response:")
print(responses.text)

