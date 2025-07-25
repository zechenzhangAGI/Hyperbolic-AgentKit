"""Debug API key issues"""

import os
from dotenv import load_dotenv

load_dotenv()

# From reference code
ref_api_key = "709KLfil8udIORZu9UjjE4jhaGTG6uW0"

# From .env
env_api_key = os.getenv("HARVARD_API_KEY")

print(f"Reference API key: {ref_api_key}")
print(f"Env API key: {env_api_key}")
print(f"Are they the same? {ref_api_key == env_api_key}")

# Test both
import requests

url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
payload = {
    "model": "o3-mini-2025-01-31",
    "messages": [{"role": "user", "content": "Hi"}],
    "temperature": 1
}

print("\nTesting reference API key:")
headers = {'Content-Type': 'application/json', 'api-key': ref_api_key}
response = requests.post(url, headers=headers, json=payload)
print(f"Status: {response.status_code}")

print("\nTesting env API key:")
headers = {'Content-Type': 'application/json', 'api-key': env_api_key}
response = requests.post(url, headers=headers, json=payload)
print(f"Status: {response.status_code}")