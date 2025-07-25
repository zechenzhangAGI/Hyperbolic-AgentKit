"""
Test Harvard API endpoint and LangChain integration.
Run with: poetry run python tests/test_harvard_api.py
"""

import os
import sys
import json
import requests
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from base_utils.llm_factory import LLMFactory
from base_utils.custom_llm_providers import HarvardChatModel

# Load environment variables
load_dotenv()


def test_direct_api_call():
    """Test 1: Direct API call to Harvard endpoint"""
    print("\n=== Test 1: Direct Harvard API Call ===")
    
    api_key = os.getenv("HARVARD_API_KEY")
    if not api_key:
        print("❌ HARVARD_API_KEY not found in environment")
        return False
    
    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    
    payload = json.dumps({
        "model": "o3-mini-2025-01-31",
        "messages": [{"role": "user", "content": "Say 'Hello from Harvard API' and nothing else."}],
        "temperature": 1
    })
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    
    try:
        print(f"Calling Harvard API endpoint...")
        print(f"URL: {url}")
        print(f"Model: o3-mini-2025-01-31")
        
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ Success! Response: {content}")
            print(f"Model used: {result.get('model', 'unknown')}")
            print(f"Usage: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


def test_harvard_chat_model():
    """Test 2: HarvardChatModel custom provider"""
    print("\n=== Test 2: HarvardChatModel Provider ===")
    
    try:
        # Create Harvard chat model directly
        harvard_model = HarvardChatModel(
            model="o3-mini-2025-01-31",
            temperature=1.0
        )
        
        print("Testing HarvardChatModel...")
        
        # Test simple call
        response = harvard_model._call([
            HumanMessage(content="What is 2+2? Just give the number.")
        ])
        
        print(f"✅ HarvardChatModel works! Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ HarvardChatModel error: {str(e)}")
        return False


def test_llm_factory():
    """Test 3: LLM Factory with Harvard provider"""
    print("\n=== Test 3: LLM Factory Harvard Provider ===")
    
    try:
        # Set environment for factory
        os.environ["LLM_PROVIDER"] = "harvard"
        os.environ["LLM_MODEL"] = "o3-mini-2025-01-31"
        
        # Create LLM via factory
        llm = LLMFactory.create_llm()
        
        print(f"Created LLM: {llm._llm_type}")
        print(f"Model: {llm.model}")
        
        # Test invoke
        messages = [
            SystemMessage(content="You are a helpful assistant. Be very concise."),
            HumanMessage(content="What is the capital of France? One word only.")
        ]
        
        response = llm.invoke(messages)
        print(f"✅ LLM Factory works! Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ LLM Factory error: {str(e)}")
        return False


async def test_langchain_integration():
    """Test 4: Full LangChain integration"""
    print("\n=== Test 4: LangChain Integration ===")
    
    try:
        from langchain.tools import Tool
        from langchain.agents import create_react_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        # Create LLM
        llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
        
        # Create a simple tool
        def get_weather(location: str) -> str:
            return f"The weather in {location} is sunny and 72°F."
        
        weather_tool = Tool(
            name="get_weather",
            description="Get the current weather for a location",
            func=get_weather
        )
        
        # Create a simple prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Note: Harvard models might not support the full ReAct pattern
        # So let's just test if we can call the LLM through LangChain
        print("Testing LangChain chain with Harvard LLM...")
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "input": "What is the meaning of life? Answer in exactly 5 words.",
            "agent_scratchpad": ""
        })
        
        print(f"✅ LangChain integration works! Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ LangChain integration error: {str(e)}")
        return False


def test_model_switching():
    """Test 5: Model switching between providers"""
    print("\n=== Test 5: Model Switching ===")
    
    try:
        # Test Harvard model
        print("Creating Harvard o3-mini model...")
        harvard_llm = LLMFactory.create_llm(
            provider="harvard",
            model="o3-mini-2025-01-31"
        )
        
        response1 = harvard_llm.invoke([
            HumanMessage(content="Say 'Harvard model active' and nothing else.")
        ])
        print(f"Harvard response: {response1.content}")
        
        # Test Harvard GPT-4.1 mini
        print("\nSwitching to Harvard GPT-4.1 mini...")
        harvard_gpt = LLMFactory.create_llm(
            provider="harvard", 
            model="gpt-4.1-mini-2025-04-14"
        )
        
        response2 = harvard_gpt.invoke([
            HumanMessage(content="Say 'GPT-4.1 mini active' and nothing else.")
        ])
        print(f"GPT-4.1 mini response: {response2.content}")
        
        print("✅ Model switching successful!")
        return True
        
    except Exception as e:
        print(f"❌ Model switching error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Harvard API Integration Tests")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("HARVARD_API_KEY")
    if not api_key:
        print("❌ HARVARD_API_KEY not found in .env file!")
        print("Please ensure your .env file contains: HARVARD_API_KEY=your_key")
        return
    
    print(f"✅ Found Harvard API key: {api_key[:10]}...")
    
    # Run tests
    tests = [
        ("Direct API Call", test_direct_api_call),
        ("HarvardChatModel", test_harvard_chat_model),
        ("LLM Factory", test_llm_factory),
        ("Model Switching", test_model_switching)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Run async test
    print("\nRunning async tests...")
    try:
        success = asyncio.run(test_langchain_integration())
        results.append(("LangChain Integration", success))
    except Exception as e:
        print(f"❌ LangChain test crashed: {str(e)}")
        results.append(("LangChain Integration", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Harvard API integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()