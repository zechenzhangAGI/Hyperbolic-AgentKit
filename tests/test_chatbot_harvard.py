"""
Test the chatbot CLI with Harvard API integration.
This simulates the core chatbot functionality with Harvard models.

Run with: poetry run python tests/test_chatbot_harvard.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain.tools import Tool
from langchain_core.runnables import RunnableConfig

from base_utils.llm_factory import LLMFactory
from base_utils.llm_commands import LLMCommands
from base_utils.utils import print_system, print_ai, print_error, Colors

# Load environment variables
load_dotenv()


def create_test_tools():
    """Create some simple tools for testing"""
    
    def calculate(expression: str) -> str:
        """Calculate a mathematical expression"""
        try:
            result = eval(expression)
            return f"The result of {expression} is {result}"
        except:
            return f"Error calculating {expression}"
    
    def get_info(topic: str) -> str:
        """Get information about a topic"""
        info_db = {
            "harvard": "Harvard University is a private Ivy League research university in Cambridge, Massachusetts.",
            "ai": "Artificial Intelligence is the simulation of human intelligence in machines.",
            "python": "Python is a high-level programming language known for its simplicity."
        }
        return info_db.get(topic.lower(), f"No information available about {topic}")
    
    return [
        Tool(
            name="calculate",
            description="Calculate mathematical expressions. Input should be a valid math expression.",
            func=calculate
        ),
        Tool(
            name="get_info",
            description="Get information about a topic. Input should be a topic name.",
            func=get_info
        )
    ]


async def test_basic_chat():
    """Test basic chat functionality with Harvard model"""
    print("\n=== Test: Basic Chat with Harvard o3-mini ===")
    
    # Create LLM
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    # Test simple conversation
    messages = [
        SystemMessage(content="You are a helpful AI assistant. Be concise."),
        HumanMessage(content="What is 15 * 23? Just give the answer.")
    ]
    
    response = await llm.ainvoke(messages)
    print(f"Response: {response.content}")
    
    # Verify response contains the answer
    if "345" in response.content:
        print("✅ Basic chat test passed!")
        return True
    else:
        print("❌ Basic chat test failed - unexpected response")
        return False


async def test_react_agent():
    """Test ReAct agent with tools using Harvard model"""
    print("\n=== Test: ReAct Agent with Harvard Model ===")
    
    try:
        # Create LLM
        llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
        
        # Create tools
        tools = create_test_tools()
        
        # Create memory
        memory = MemorySaver()
        
        # Create agent
        agent = create_react_agent(
            llm,
            tools=tools,
            checkpointer=memory,
        )
        
        # Create config
        config = RunnableConfig(
            configurable={
                "thread_id": "test-thread",
            }
        )
        
        # Test 1: Simple calculation
        print("\nTest 1: Asking agent to calculate...")
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="What is 123 + 456?")]},
            config
        )
        
        last_message = result["messages"][-1].content
        print(f"Agent response: {last_message}")
        
        if "579" in last_message:
            print("✅ Calculation test passed!")
        else:
            print("❌ Calculation test failed")
        
        # Test 2: Information retrieval
        print("\nTest 2: Asking for information...")
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="Tell me about Harvard")]},
            config
        )
        
        last_message = result["messages"][-1].content
        print(f"Agent response: {last_message}")
        
        if "Harvard" in last_message or "university" in last_message.lower():
            print("✅ Information retrieval test passed!")
        else:
            print("❌ Information retrieval test failed")
        
        return True
        
    except Exception as e:
        print(f"❌ ReAct agent test failed with error: {str(e)}")
        return False


async def test_model_switching_cli():
    """Test model switching functionality as in CLI"""
    print("\n=== Test: Model Switching (CLI Simulation) ===")
    
    # Set initial model
    os.environ["LLM_PROVIDER"] = "harvard"
    os.environ["LLM_MODEL"] = "o3-mini-2025-01-31"
    
    # Test /model command to show current
    print("\nSimulating: /model")
    handled = LLMCommands.handle_model_command("/model")
    
    # Test switching to GPT-4.1 mini
    print("\nSimulating: /model harvard gpt-4.1-mini-2025-04-14")
    handled = LLMCommands.handle_model_command("/model harvard gpt-4.1-mini-2025-04-14")
    
    if handled:
        # Verify the switch
        new_model = os.getenv("LLM_MODEL")
        if new_model == "gpt-4.1-mini-2025-04-14":
            print("✅ Model switching test passed!")
            return True
    
    print("❌ Model switching test failed")
    return False


async def test_full_chat_simulation():
    """Simulate a full chat session like the CLI"""
    print("\n=== Test: Full Chat Session Simulation ===")
    
    try:
        # Set Harvard as provider
        os.environ["LLM_PROVIDER"] = "harvard"
        os.environ["LLM_MODEL"] = "o3-mini-2025-01-31"
        
        # Create components
        llm = LLMFactory.create_llm()
        tools = create_test_tools()
        memory = MemorySaver()
        
        # System prompt (simulating character)
        system_prompt = """You are Dr. Nova, an AI Research Scientist specializing in distributed computing and neural architectures.
        You are helpful, precise, and focused on practical solutions."""
        
        # State modifier function
        def state_modifier(state):
            return [
                SystemMessage(content=system_prompt),
                *state["messages"]
            ]
        
        # Create agent
        agent = create_react_agent(
            llm,
            tools=tools,
            checkpointer=memory,
            state_modifier=state_modifier
        )
        
        config = RunnableConfig(
            configurable={
                "thread_id": "Dr. Nova Agent",
            }
        )
        
        # Simulate conversation
        print("\nStarting simulated chat session...")
        print(f"{Colors.BLUE}User:{Colors.ENDC} Hello Dr. Nova! Can you help me calculate 42 * 37?")
        
        # Process message
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="Hello Dr. Nova! Can you help me calculate 42 * 37?")]},
            config
        )
        
        response = result["messages"][-1].content
        print(f"{Colors.GREEN}Dr. Nova:{Colors.ENDC} {response}")
        
        # Check if calculation was performed
        if "1554" in response:
            print("\n✅ Full chat simulation passed!")
            return True
        else:
            print("\n❌ Full chat simulation failed - calculation not performed correctly")
            return False
            
    except Exception as e:
        print(f"\n❌ Full chat simulation failed with error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Chatbot Harvard Integration Tests")
    print("=" * 60)
    
    # Check Harvard API key
    if not os.getenv("HARVARD_API_KEY"):
        print("❌ HARVARD_API_KEY not found in environment!")
        return
    
    print(f"✅ Using Harvard API key: {os.getenv('HARVARD_API_KEY')[:10]}...")
    
    # Run tests
    tests = [
        ("Basic Chat", test_basic_chat),
        ("ReAct Agent", test_react_agent),
        ("Model Switching", test_model_switching_cli),
        ("Full Chat Simulation", test_full_chat_simulation)
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
        print("\n🎉 All tests passed! The chatbot works correctly with Harvard API.")
        print("\nYou can now run the chatbot with Harvard models:")
        print("  poetry run python chatbot.py")
        print("\nThen use commands like:")
        print("  /model harvard o3-mini-2025-01-31")
        print("  /model harvard-gpt4-mini")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())