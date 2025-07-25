"""
Debug tool calling with Harvard API.
Let's see exactly what's happening when we try to use tools.

Run with: poetry run python tests/test_tool_calling.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.tools import Tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
import langchain

from base_utils.llm_factory import LLMFactory

# Load environment variables
load_dotenv()

# Enable debug mode to see what's happening
langchain.debug = True


def simple_add(a: int, b: int) -> str:
    """Add two numbers together."""
    return f"The sum of {a} and {b} is {a + b}"


def simple_multiply(a: int, b: int) -> str:
    """Multiply two numbers together."""
    return f"The product of {a} and {b} is {a * b}"


async def test_direct_tool_calling():
    """Test if the model supports tool calling directly"""
    print("\n=== Test: Direct Tool Calling ===")
    
    # Create LLM
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    # Define tools in OpenAI function format
    tools = [
        {
            "type": "function",
            "function": {
                "name": "add_numbers",
                "description": "Add two numbers together",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            }
        }
    ]
    
    # Try to bind tools to the model
    try:
        print("Attempting to bind tools to the model...")
        llm_with_tools = llm.bind_tools(tools)
        print("✅ Tools bound successfully!")
        
        # Now try to invoke with tools
        print("\nInvoking model with tool-calling request...")
        response = await llm_with_tools.ainvoke([
            HumanMessage(content="What is 15 + 27? Please use the add_numbers tool.")
        ])
        
        print(f"Response type: {type(response)}")
        print(f"Response content: {response.content}")
        
        # Check if tool_calls exist
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"✅ Tool calls detected: {response.tool_calls}")
            return True
        else:
            print("❌ No tool calls in response")
            if hasattr(response, 'additional_kwargs'):
                print(f"Additional kwargs: {response.additional_kwargs}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_langchain_tools():
    """Test using LangChain Tool objects"""
    print("\n=== Test: LangChain Tools ===")
    
    # Create LLM
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    # Create LangChain tools
    add_tool = Tool(
        name="add_numbers",
        description="Add two numbers. Input should be two numbers separated by comma, e.g., '5,3'",
        func=lambda x: str(sum(map(int, x.split(','))))
    )
    
    multiply_tool = Tool(
        name="multiply_numbers", 
        description="Multiply two numbers. Input should be two numbers separated by comma, e.g., '5,3'",
        func=lambda x: str(eval(x.replace(',', '*')))
    )
    
    tools = [add_tool, multiply_tool]
    
    try:
        print("Creating ReAct agent with tools...")
        
        # Create agent
        agent = create_react_agent(
            llm,
            tools=tools,
            checkpointer=MemorySaver()
        )
        
        config = RunnableConfig(
            configurable={"thread_id": "test"}
        )
        
        print("\nAsking agent to use tools...")
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="Calculate 25 + 17 using the add tool")]},
            config
        )
        
        print(f"\nNumber of messages in result: {len(result['messages'])}")
        for i, msg in enumerate(result['messages']):
            print(f"Message {i}: {type(msg).__name__}")
            print(f"  Content: {msg.content[:100] if msg.content else 'No content'}...")
            if hasattr(msg, 'tool_calls'):
                print(f"  Tool calls: {msg.tool_calls}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_manual_tool_format():
    """Test if we can manually format tool calls"""
    print("\n=== Test: Manual Tool Call Format ===")
    
    # Try the exact format that OpenAI uses
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    messages = [
        SystemMessage(content="You are a helpful assistant with access to tools."),
        HumanMessage(content="What is 15 + 27? Please calculate this.")
    ]
    
    # Add tools to the request manually
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
    
    # Try to see what the raw API accepts
    print("Testing what format the API accepts...")
    
    # This is closer to what the raw API might expect
    try:
        # Get the underlying model if possible
        if hasattr(llm, '_call'):
            print("Using HarvardChatModel's _call method...")
            response = llm._call(messages)
            print(f"Response: {response}")
        else:
            print("Using standard invoke...")
            response = await llm.ainvoke(messages)
            print(f"Response: {response.content}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    return True


async def test_prompt_engineering():
    """Test if we can get the model to simulate tool use through prompting"""
    print("\n=== Test: Prompt Engineering for Tools ===")
    
    llm = LLMFactory.create_llm(provider="harvard", model="o3-mini-2025-01-31")
    
    # Try to get the model to output tool calls in a specific format
    system_prompt = """You are an AI assistant that can use tools. When you need to use a tool, respond with:

TOOL_CALL: tool_name
ARGS: {argument_json}

Available tools:
- calculate: Performs math calculations. Args: {"expression": "math expression"}
- get_weather: Gets weather for a location. Args: {"location": "city name"}

After stating TOOL_CALL, wait for the result before continuing."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="What is 25 * 4? Please calculate this for me.")
    ]
    
    response = await llm.ainvoke(messages)
    print(f"Response: {response.content}")
    
    # Check if model follows the format
    if "TOOL_CALL:" in response.content:
        print("✅ Model can follow tool-calling format through prompting!")
        return True
    else:
        print("❌ Model didn't follow the tool format")
        return False


async def main():
    """Run all tool calling tests"""
    print("=" * 60)
    print("Tool Calling Debug Tests")
    print("=" * 60)
    
    tests = [
        ("Direct Tool Calling", test_direct_tool_calling),
        ("LangChain Tools", test_langchain_tools),
        ("Manual Format", test_manual_tool_format),
        ("Prompt Engineering", test_prompt_engineering)
    ]
    
    results = []
    
    # Temporarily disable debug for cleaner output
    langchain.debug = False
    
    for name, test_func in tests:
        try:
            # Re-enable debug for the actual test
            if name == "LangChain Tools":
                langchain.debug = True
            
            success = await test_func()
            results.append((name, success))
            
            # Disable debug again
            langchain.debug = False
            
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 60)
    print("Conclusion:")
    print("=" * 60)
    
    if results[0][1]:  # If direct tool calling passed
        print("✅ Harvard models DO support tool calling!")
        print("The issue might be in the configuration or integration.")
    else:
        print("❌ Harvard models don't support native tool calling.")
        print("But we can work around this with prompt engineering!")


if __name__ == "__main__":
    asyncio.run(main())