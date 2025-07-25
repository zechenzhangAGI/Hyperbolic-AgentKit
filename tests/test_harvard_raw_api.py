"""
Test Harvard API directly to understand what it supports.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_without_tools():
    """Test basic API call without tools"""
    print("=== Test 1: Basic API Call (No Tools) ===")
    
    api_key = os.getenv("HARVARD_API_KEY")
    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    
    payload = {
        "model": "o3-mini-2025-01-31",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "temperature": 1
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()['choices'][0]['message']['content']}")
    else:
        print(f"Error: {response.text}")


def test_with_tools():
    """Test API call with tools parameter"""
    print("\n=== Test 2: API Call with Tools ===")
    
    api_key = os.getenv("HARVARD_API_KEY")
    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    
    # Standard OpenAI tools format
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
    
    payload = {
        "model": "o3-mini-2025-01-31",
        "messages": [{"role": "user", "content": "What is 15 + 27? Use the calculate tool."}],
        "temperature": 1,
        "tools": tools,
        "tool_choice": "auto"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.text}")


def test_with_functions():
    """Test API call with functions parameter (older format)"""
    print("\n=== Test 3: API Call with Functions (Old Format) ===")
    
    api_key = os.getenv("HARVARD_API_KEY")
    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    
    # Older OpenAI functions format
    functions = [
        {
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
    ]
    
    payload = {
        "model": "o3-mini-2025-01-31",
        "messages": [{"role": "user", "content": "What is 15 + 27? Use the calculate function."}],
        "temperature": 1,
        "functions": functions,
        "function_call": "auto"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.text}")


def test_system_message_tools():
    """Test if we can simulate tools through system message"""
    print("\n=== Test 4: System Message Tool Simulation ===")
    
    api_key = os.getenv("HARVARD_API_KEY")
    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    
    system_msg = """You are an AI assistant with access to the following tools:

1. calculate(expression: str) - Performs mathematical calculations
2. get_weather(location: str) - Gets weather information

When you need to use a tool, respond EXACTLY in this format:
<tool_use>
{"tool": "tool_name", "arguments": {"arg1": "value1"}}
</tool_use>

Then wait for the tool result before continuing."""
    
    payload = {
        "model": "o3-mini-2025-01-31",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "What is 156 * 23?"}
        ],
        "temperature": 1
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"Response: {content}")
        
        # Check if model followed the format
        if "<tool_use>" in content:
            print("✅ Model can simulate tool use through prompting!")
        else:
            print("❌ Model didn't follow tool format")
    else:
        print(f"Error: {response.text}")


def test_available_endpoints():
    """Test what endpoints are available"""
    print("\n=== Test 5: Available Endpoints ===")
    
    api_key = os.getenv("HARVARD_API_KEY")
    base_url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1"
    
    headers = {
        'api-key': api_key
    }
    
    # Try common OpenAI endpoints
    endpoints = [
        "/models",
        "/chat/completions",
        "/completions",
        "/embeddings"
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            if endpoint == "/models":
                response = requests.get(url, headers=headers)
            else:
                # Just check if endpoint exists
                response = requests.options(url, headers=headers)
            
            print(f"{endpoint}: {response.status_code}")
            
            if endpoint == "/models" and response.status_code == 200:
                models = response.json()
                print(f"  Available models: {json.dumps(models, indent=2)}")
        except Exception as e:
            print(f"{endpoint}: Error - {str(e)}")


if __name__ == "__main__":
    print("Harvard API Capability Tests")
    print("=" * 60)
    
    test_without_tools()
    test_with_tools()
    test_with_functions()
    test_system_message_tools()
    test_available_endpoints()