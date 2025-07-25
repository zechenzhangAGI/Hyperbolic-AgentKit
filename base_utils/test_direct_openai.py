"""Test using OpenAI Python client directly with Harvard endpoint"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Create client with Harvard endpoint
client = OpenAI(
    api_key=os.getenv("HARVARD_API_KEY"),
    base_url="https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1",
    default_headers={
        "api-key": os.getenv("HARVARD_API_KEY")
    }
)

# Test basic call
print("=== Test 1: Basic Call ===")
response = client.chat.completions.create(
    model="o3-mini-2025-01-31",
    messages=[{"role": "user", "content": "Say hello"}],
    temperature=1
)
print(f"Response: {response.choices[0].message.content}")

# Test with tools
print("\n=== Test 2: With Tools ===")
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="o3-mini-2025-01-31",
    messages=[{"role": "user", "content": "What is 15 + 27? Use the calculate tool."}],
    tools=tools,
    temperature=1
)

print(f"Response: {response.choices[0].message}")
if response.choices[0].message.tool_calls:
    print(f"Tool calls: {response.choices[0].message.tool_calls}")