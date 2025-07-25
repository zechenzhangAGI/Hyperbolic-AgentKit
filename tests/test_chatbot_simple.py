"""
Simple chatbot test without ReAct/tools for Harvard API.
This tests the core chat functionality that will work with any LLM.

Run with: poetry run python tests/test_chatbot_simple.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from base_utils.llm_factory import LLMFactory
from base_utils.utils import print_system, print_ai, print_error, Colors

# Load environment variables
load_dotenv()


async def test_simple_conversation():
    """Test a simple multi-turn conversation"""
    print("\n=== Test: Simple Multi-turn Conversation ===")
    
    # Create LLM
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    # Initialize conversation
    messages = [
        SystemMessage(content="You are Dr. Nova, an AI assistant. Be helpful and concise.")
    ]
    
    # Turn 1
    print(f"\n{Colors.BLUE}User:{Colors.ENDC} Hello! What's 2+2?")
    messages.append(HumanMessage(content="Hello! What's 2+2?"))
    
    response = await llm.ainvoke(messages)
    print(f"{Colors.GREEN}Dr. Nova:{Colors.ENDC} {response.content}")
    messages.append(response)
    
    # Turn 2
    print(f"\n{Colors.BLUE}User:{Colors.ENDC} Great! Now multiply that by 10.")
    messages.append(HumanMessage(content="Great! Now multiply that by 10."))
    
    response = await llm.ainvoke(messages)
    print(f"{Colors.GREEN}Dr. Nova:{Colors.ENDC} {response.content}")
    
    # Check if conversation maintains context
    if "40" in response.content or "forty" in response.content.lower():
        print("\n✅ Conversation context maintained!")
        return True
    else:
        print("\n❌ Conversation context lost")
        return False


async def test_different_models():
    """Test switching between Harvard models"""
    print("\n=== Test: Different Harvard Models ===")
    
    models = [
        ("o3-mini-2025-01-31", "Harvard o3-mini"),
        ("gpt-4.1-mini-2025-04-14", "Harvard GPT-4.1 mini")
    ]
    
    for model_id, model_name in models:
        print(f"\nTesting {model_name}...")
        
        try:
            llm = LLMFactory.create_llm(provider="harvard", model=model_id)
            
            response = await llm.ainvoke([
                HumanMessage(content=f"Say 'Hello from {model_name}' and nothing else.")
            ])
            
            print(f"Response: {response.content}")
            
            if model_name.lower() in response.content.lower() or "hello" in response.content.lower():
                print(f"✅ {model_name} working!")
            else:
                print(f"❌ {model_name} unexpected response")
                
        except Exception as e:
            print(f"❌ {model_name} failed: {str(e)}")
            return False
    
    return True


async def test_streaming_simulation():
    """Simulate streaming responses (even if not truly streaming)"""
    print("\n=== Test: Streaming Simulation ===")
    
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    print(f"\n{Colors.BLUE}User:{Colors.ENDC} Tell me a joke about programming.")
    
    # For Harvard API, we can't truly stream, but we can simulate the behavior
    response = await llm.ainvoke([
        SystemMessage(content="You are a funny AI assistant."),
        HumanMessage(content="Tell me a joke about programming.")
    ])
    
    # Simulate streaming by printing word by word
    print(f"{Colors.GREEN}Dr. Nova:{Colors.ENDC} ", end="")
    words = response.content.split()
    for i, word in enumerate(words):
        print(word, end=" ")
        if i < len(words) - 1:
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
    print()  # New line at end
    
    print("\n✅ Streaming simulation completed!")
    return True


async def test_error_handling():
    """Test error handling scenarios"""
    print("\n=== Test: Error Handling ===")
    
    # Test 1: Invalid model
    print("\nTest 1: Invalid model name...")
    try:
        llm = LLMFactory.create_llm(provider="harvard", model="invalid-model")
        # If we get here, try to use it
        response = await llm.ainvoke([HumanMessage(content="test")])
        print("❌ Should have failed with invalid model")
        return False
    except Exception as e:
        print(f"✅ Correctly caught error: {str(e)[:100]}...")
    
    # Test 2: Empty API key
    print("\nTest 2: Missing API key...")
    original_key = os.environ.get("HARVARD_API_KEY")
    try:
        os.environ.pop("HARVARD_API_KEY", None)
        llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
        print("❌ Should have failed with missing API key")
        return False
    except ValueError as e:
        print(f"✅ Correctly caught error: {e}")
    finally:
        if original_key:
            os.environ["HARVARD_API_KEY"] = original_key
    
    return True


async def main():
    """Run all simple tests"""
    print("=" * 60)
    print("Simple Chatbot Tests (No Tools/ReAct)")
    print("=" * 60)
    
    # Check Harvard API key
    if not os.getenv("HARVARD_API_KEY"):
        print("❌ HARVARD_API_KEY not found in environment!")
        return
    
    print(f"✅ Using Harvard API key: {os.getenv('HARVARD_API_KEY')[:10]}...")
    
    # Run tests
    tests = [
        ("Simple Conversation", test_simple_conversation),
        ("Different Models", test_different_models),
        ("Streaming Simulation", test_streaming_simulation),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
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
        print("\n🎉 All tests passed!")
        print("\nThe chatbot will work with Harvard models for chat conversations.")
        print("Note: Harvard models may not support advanced features like tool calling.")
        print("\nTo use with the chatbot:")
        print("  1. Ensure your .env has: HARVARD_API_KEY=your_key")
        print("  2. Run: poetry run python chatbot.py")
        print("  3. The chat will work, but tools (browser, hyperbolic, etc.) may not function")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())