# How ReAct is Actually Implemented

## The Truth: It's More Than Just a Prompt

ReAct (Reasoning + Acting) in LangGraph is implemented through:
1. **Structured message flow**
2. **Tool calling capabilities**
3. **State machine orchestration**
4. **NOT through explicit "Thought/Action/Observation" prompting**

## 1. What ReAct Originally Was (Paper Version)

The original ReAct paper used explicit prompting:
```
Question: What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?

Thought 1: I need to search Colorado orogeny, find the area that the eastern sector extends into, then find the elevation range of that area.
Action 1: Search[Colorado orogeny]
Observation 1: The Colorado orogeny was an episode of mountain building...

Thought 2: It does not mention the eastern sector. So I need to look up eastern sector.
Action 2: Lookup[eastern sector]
Observation 2: (Result 1 / 1) The eastern sector extends into the High Plains...

Thought 3: The eastern sector extends into the High Plains. I need to search High Plains and find its elevation range.
Action 3: Search[High Plains]
Observation 3: ...
```

## 2. How LangGraph Actually Implements ReAct

### The Core Implementation (Simplified)

```python
# This is conceptually what create_react_agent does:

def react_agent_loop(messages, tools, llm):
    while True:
        # 1. LLM sees messages and available tools
        response = llm.invoke(
            messages,
            tools=tools,  # Tools are passed as function schemas
        )
        
        # 2. If LLM wants to use tools (Acting)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Execute the tool
                tool_result = execute_tool(tool_call)
                
                # Add result to messages
                messages.append(ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call.id
                ))
        else:
            # No more tools needed, return final answer
            return response
```

### Key Insight: No Explicit "Thought/Action/Observation" Text

Modern LLMs like Claude use **structured tool calling** instead of text patterns:

```python
# Old ReAct style (text-based):
"Thought: I need to check available GPUs\nAction: get_available_gpus()\n"

# Modern LangGraph style (structured):
AIMessage(
    content="I'll check the available GPUs for you.",
    tool_calls=[{
        "id": "call_123",
        "name": "get_available_gpus",
        "args": {}
    }]
)
```

## 3. The Actual LangGraph Implementation

Let's look at the real implementation pattern:

### State Definition
```python
# From langgraph source
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    is_last_step: IsLastStep

# The state tracks messages and whether we're done
```

### The Graph Structure
```python
# Conceptually, create_react_agent builds this graph:

def create_react_agent(model, tools, ...):
    # Create nodes
    def agent_node(state):
        # Call LLM with current messages
        response = model.invoke(
            state["messages"],
            tools=tools  # Pass tool schemas
        )
        return {"messages": [response]}
    
    def tool_node(state):
        # Execute any tool calls from last message
        last_message = state["messages"][-1]
        tool_messages = []
        
        for tool_call in last_message.tool_calls:
            tool = get_tool_by_name(tool_call["name"])
            result = tool.invoke(tool_call["args"])
            tool_messages.append(
                ToolMessage(content=result, tool_call_id=tool_call["id"])
            )
        
        return {"messages": tool_messages}
    
    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    
    # Conditional edge: if agent calls tools, go to tools node
    workflow.add_conditional_edges(
        "agent",
        should_continue,  # Checks if tool_calls exist
        {
            "continue": "tools",
            "end": END,
        }
    )
    
    # After tools, always go back to agent
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
```

### The Should Continue Logic
```python
def should_continue(state):
    last_message = state["messages"][-1]
    
    # If the LLM called tools, continue to tool node
    if last_message.tool_calls:
        return "continue"
    
    # Otherwise, we're done
    return "end"
```

## 4. How Tool Calling Works Under the Hood

### What the LLM Actually Sees

```python
# When you call the agent, the LLM receives:
{
    "messages": [...],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "remote_write_file",
                "description": "This tool will write content to a file...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                        "append": {"type": "boolean", "default": false}
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        # ... more tools
    ]
}
```

### The LLM's Response Format
```python
# Claude responds with structured tool calls:
{
    "content": "I'll create that file for you.",
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "remote_write_file",
                "arguments": '{"file_path": "test.py", "content": "print(\'hello\')"}'
            }
        }
    ]
}
```

## 5. No Explicit ReAct Prompting!

### What You DON'T See
There's no prompt saying:
```
"You must follow this format:
Thought: Your reasoning
Action: tool_name(args)
Observation: Tool result"
```

### What Actually Happens
1. **Implicit Reasoning**: Claude reasons internally based on its training
2. **Structured Output**: Uses native tool-calling format
3. **Graph Orchestration**: LangGraph handles the loop

## 6. The State Modifier (Character Prompt)

The only prompting that happens is the character/system prompt:

```python
def state_modifier(state):
    # This is where personality is injected
    system_prompt = """
    You are Dr. Nova, an AI Research Scientist...
    Bio: ...
    Knowledge: ...
    Style: ...
    """
    
    return [
        SystemMessage(content=system_prompt),
        *state["messages"]
    ]
```

## 7. Why This Design?

### Old Way (Text-Based ReAct)
- Fragile parsing of "Action: tool_name(args)"
- LLM might format incorrectly
- Needed complex regex parsing

### New Way (Structured Tool Calling)
- LLM outputs structured JSON
- No parsing needed
- More reliable
- Native to modern LLMs

## 8. The Complete Flow

```
1. User Message
   ↓
2. Agent Node
   - LLM sees: messages + available tools
   - LLM outputs: response + tool_calls (if needed)
   ↓
3. Should Continue?
   - If tool_calls exist → go to Tools Node
   - If no tool_calls → End
   ↓
4. Tools Node (if needed)
   - Execute each tool call
   - Create ToolMessages with results
   ↓
5. Back to Agent Node
   - LLM sees: original messages + tool results
   - LLM can call more tools or give final answer
   ↓
6. Repeat until no more tool calls
```

## 9. Debugging: See ReAct in Action

```python
import langchain
langchain.debug = True

# You'll see the actual flow:
"""
[agent] Entering node
  Input: {'messages': [HumanMessage('Create a file')]}
  Calling LLM with tools...
  
[agent] LLM Response:
  content: "I'll create that file"
  tool_calls: [{'name': 'remote_write_file', ...}]
  
[tools] Entering node
  Executing remote_write_file...
  Result: "Successfully written"
  
[agent] Entering node again
  Input: {'messages': [..., ToolMessage('Successfully written')]}
  LLM Response: "I've created the file successfully"
  
[end] No more tool calls, ending
"""
```

## Summary

**ReAct in LangGraph is NOT implemented as a text prompt pattern!**

Instead, it's:
1. **A graph structure** with agent and tool nodes
2. **Native tool calling** in the LLM
3. **State machine logic** to orchestrate the loop
4. **Implicit reasoning** by the LLM (not explicit "Thought:" prompts)

The "Reasoning" happens inside Claude's neural networks, and the "Acting" happens through structured tool calls. LangGraph just orchestrates the loop between them.

This is why it's more robust than the original ReAct - no fragile text parsing, just structured data flow!