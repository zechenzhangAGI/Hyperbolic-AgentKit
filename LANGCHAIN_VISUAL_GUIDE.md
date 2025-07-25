# LangChain Chatbot Visual Guide

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                         │
│                     (Terminal / Gradio)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ User Input
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph ReAct Agent                      │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │   Memory     │   │  Character   │   │   Tool Router   │  │
│  │  (History)   │   │ (Personality)│   │                 │  │
│  └─────────────┘   └──────────────┘   └─────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Claude Sonnet 4 LLM                        │
│                  (Reasoning & Decision)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ Tool Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        Tool Layer                             │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐  │
│  │ Hyperbolic │  │  Browser   │  │  Coinbase/Twitter    │  │
│  │   Tools    │  │   Tools    │  │      Tools            │  │
│  └────────────┘  └────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 2. Initialization Flow

```
START
  │
  ▼
Load Environment Variables (.env)
  │
  ▼
Initialize LLM (Claude Sonnet 4)
  │
  ▼
Load Character Config (e.g., dr_nova.json)
  │
  ├─> Extract: Bio, Knowledge, Style
  │
  ▼
Create Tools
  │
  ├─> IF USE_HYPERBOLIC_TOOLS=true
  │     └─> Load: rent_compute, ssh_connect, remote_write_file, etc.
  │
  ├─> IF USE_BROWSER_TOOLS=true
  │     └─> Load: navigate_browser, click, type, etc.
  │
  ├─> IF USE_COINBASE_TOOLS=true
  │     └─> Load: send_transaction, deploy_nft, etc.
  │
  ▼
Create ReAct Agent
  │
  ├─> LLM + Tools + Memory + Personality
  │
  ▼
Start Chat Loop
```

## 3. Message Flow Diagram

```
User: "Create a training script for MNIST"
         │
         ▼
┌────────────────────────────────────┐
│   1. Message Preprocessing         │
│   - Create HumanMessage object     │
│   - Add to message history         │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│   2. State Modifier                │
│   - Prepend character personality  │
│   - Format: [System, Human, ...]   │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│   3. LLM Processing                │
│   - Sees full context              │
│   - Reasons about task             │
│   - Decides on action              │
└────────────────────────────────────┘
         │
         ▼
    Should I use a tool?
         │
    ┌────┴────┐
    │   NO    │ YES
    ▼         ▼
 Return    Tool Call
 Answer
```

## 4. ReAct Loop Visualization

```
┌─────────────────────────────────────────────────┐
│                  ReAct Cycle                     │
│                                                  │
│   ┌──────────┐      ┌──────────┐               │
│   │ OBSERVE  │ ───> │  THINK   │               │
│   └──────────┘      └──────────┘               │
│        ▲                  │                     │
│        │                  ▼                     │
│   ┌──────────┐      ┌──────────┐               │
│   │  RESULT  │ <─── │   ACT    │               │
│   └──────────┘      └──────────┘               │
│                                                  │
└─────────────────────────────────────────────────┘

Example Trace:
1. OBSERVE: "User wants MNIST training script"
2. THINK: "I need to create a Python file with PyTorch code"
3. ACT: Call remote_write_file(file_path="train_mnist.py", content="...")
4. RESULT: "Successfully written to 'train_mnist.py'"
5. OBSERVE: "File created successfully"
6. THINK: "Now I should run it to test"
7. ACT: Call remote_shell(command="python train_mnist.py")
8. RESULT: "Training started... Epoch 1/10..."
9. OBSERVE: "Training is running"
10. THINK: "Task complete, summarize for user"
11. Return final response
```

## 5. Tool Calling Flow

```
Agent decides to use tool: remote_write_file
                │
                ▼
┌─────────────────────────────────────┐
│        Tool Call Format             │
│ {                                   │
│   "name": "remote_write_file",      │
│   "args": {                         │
│     "file_path": "script.py",      │
│     "content": "print('hello')"    │
│   }                                 │
│ }                                   │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│      LangGraph Execution            │
│ 1. Validate against schema          │
│ 2. Call the actual function         │
│ 3. Capture result                   │
│ 4. Create ToolMessage               │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│         Tool Function               │
│ def write_remote_file(...):         │
│   - Check SSH connection            │
│   - Create directories              │
│   - Write file                      │
│   - Return status                   │
└─────────────────────────────────────┘
                │
                ▼
         Result: "Success"
```

## 6. Memory State Structure

```
Conversation State:
{
  "messages": [
    {
      "type": "system",
      "content": "You are Dr. Nova..."
    },
    {
      "type": "human", 
      "content": "Create a training script"
    },
    {
      "type": "ai",
      "content": "I'll create a PyTorch training script...",
      "tool_calls": [{
        "id": "call_123",
        "name": "remote_write_file",
        "args": {...}
      }]
    },
    {
      "type": "tool",
      "tool_call_id": "call_123",
      "content": "Successfully written..."
    },
    {
      "type": "ai",
      "content": "I've created the training script..."
    }
  ],
  "thread_id": "Dr. Nova Agent",
  "checkpoint_id": "abc-123",
  "metadata": {
    "character": "Dr. Nova",
    "session_start": "2024-07-24T10:00:00Z"
  }
}
```

## 7. Complete Interaction Example

```
┌─────────────────┐
│      USER       │
└────────┬────────┘
         │ "Help me train a model on CIFAR-10"
         ▼
┌─────────────────┐
│  STATE MODIFIER │ Adds: "You are Dr. Nova, AI Research Scientist..."
└────────┬────────┘
         ▼
┌─────────────────┐
│   CLAUDE LLM    │ Thinks: "Need GPU, create script, setup env"
└────────┬────────┘
         ▼
┌─────────────────┐
│ get_available_  │
│     gpus()      │ Returns: [{A100, 80GB}, {V100, 16GB}]
└────────┬────────┘
         ▼
┌─────────────────┐
│  rent_compute() │ Returns: "Rented A100, SSH: user@1.2.3.4"
└────────┬────────┘
         ▼
┌─────────────────┐
│  ssh_connect()  │ Returns: "Connected successfully"
└────────┬────────┘
         ▼
┌─────────────────┐
│remote_write_file│ Creates: train_cifar10.py
└────────┬────────┘
         ▼
┌─────────────────┐
│ remote_shell()  │ Runs: "python train_cifar10.py"
└────────┬────────┘
         ▼
┌─────────────────┐
│   CLAUDE LLM    │ "I've set up CIFAR-10 training on an A100 GPU..."
└────────┬────────┘
         ▼
┌─────────────────┐
│      USER       │ Sees formatted response
└─────────────────┘
```

## 8. Error Handling Flow

```
Tool Call Attempt
       │
       ▼
   Validation
       │
   ┌───┴───┐
   │ FAIL  │ PASS
   ▼       ▼
Error    Execute
Message   Tool
   │       │
   ▼       ▼
Agent    Success
Retry    Result
   │       │
   └───┬───┘
       ▼
   Continue
```

This visual guide shows how all the pieces fit together to create an intelligent, tool-using AI assistant!