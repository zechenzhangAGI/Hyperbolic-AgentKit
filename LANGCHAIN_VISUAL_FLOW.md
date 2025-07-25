# Visual Flow Diagrams for LangChain Chatbot

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CHATBOT SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐     ┌────────────┐     ┌─────────────┐       │
│  │   User   │ ──> │  LangChain │ ──> │   Claude    │       │
│  │  Input   │     │   Agent    │     │   (LLM)     │       │
│  └──────────┘     └────────────┘     └─────────────┘       │
│        ↑                 │                    │              │
│        │                 ↓                    ↓              │
│        │          ┌────────────┐      ┌─────────────┐       │
│        └────────  │   Memory   │      │    Tools    │       │
│                   │  (State)   │      │ (Functions) │       │
│                   └────────────┘      └─────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 2. Tool Registration Flow

```
startup
   │
   ├─> Load Environment Variables
   │     └─> USE_HYPERBOLIC_TOOLS=true
   │     └─> USE_BROWSER_TOOLS=true
   │     └─> etc.
   │
   ├─> Discover Tools
   │     └─> hyperbolic_agentkit_core/actions/__init__.py
   │           └─> get_all_hyperbolic_actions()
   │                 └─> Finds all HyperbolicAction subclasses
   │                       ├─> RemoteShellAction
   │                       ├─> RemoteWriteFileAction
   │                       ├─> RentComputeAction
   │                       └─> ... (16 total)
   │
   └─> Create LangChain Tools
         └─> For each action:
               Tool(
                 name=action.name,
                 description=action.description,
                 func=action.func,
                 args_schema=action.args_schema
               )
```

## 3. Message Flow - Detailed Example

```
User: "Create a Python script to train a neural network"
         │
         ↓
┌─────────────────────────────────────────────────────┐
│              LANGCHAIN AGENT PROCESS                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Receive Message                                  │
│     HumanMessage("Create a Python script...")        │
│                      │                               │
│                      ↓                               │
│  2. Send to Claude with Context                      │
│     ┌──────────────────────────────────────┐        │
│     │ System: You are Dr. Nova...          │        │
│     │                                       │        │
│     │ Tools Available:                      │        │
│     │ - remote_write_file: Write files...  │        │
│     │ - remote_shell: Execute commands...  │        │
│     │ - remote_read_file: Read files...    │        │
│     │                                       │        │
│     │ Messages:                             │        │
│     │ Human: Create a Python script...      │        │
│     └──────────────────────────────────────┘        │
│                      │                               │
│                      ↓                               │
│  3. Claude Decides to Use Tool                       │
│     Thought: "I need to create a file with          │
│              training code"                          │
│     Action: remote_write_file                        │
│                      │                               │
│                      ↓                               │
│  4. Tool Call Structure                              │
│     {                                                │
│       "tool": "remote_write_file",                   │
│       "args": {                                      │
│         "file_path": "train_nn.py",                  │
│         "content": "import torch\\n..."              │
│       }                                              │
│     }                                                │
│                      │                               │
│                      ↓                               │
│  5. LangChain Validates & Executes                   │
│     - Check args match schema ✓                      │
│     - Call write_remote_file()                       │
│     - Return result                                  │
│                      │                               │
│                      ↓                               │
│  6. Tool Result                                      │
│     "Successfully written to 'train_nn.py'"          │
│                      │                               │
│                      ↓                               │
│  7. Claude Sees Result & Responds                    │
│     "I've created train_nn.py with a basic          │
│      neural network training script..."              │
│                                                      │
└─────────────────────────────────────────────────────┘
         │
         ↓
Dr. Nova: I've created train_nn.py with a basic neural network 
         training script. The script includes:
         - PyTorch model definition
         - Training loop
         - Loss calculation
         - Basic logging
```

## 4. ReAct Loop Pattern

```
┌─────────────────────────────────────────────────────┐
│                   ReAct LOOP                         │
│                                                      │
│   ┌────────┐    ┌─────────┐    ┌────────┐         │
│   │Observe │ -> │ Reason  │ -> │  Act   │         │
│   └────────┘    └─────────┘    └────────┘         │
│       ↑                              │               │
│       └──────────────────────────────┘               │
│                                                      │
│   Example Trace:                                     │
│                                                      │
│   1. Observe: "User wants to train a model"         │
│   2. Reason:  "I need to check available GPUs"      │
│   3. Act:     get_available_gpus()                  │
│   4. Observe: "A100 and V100 available"             │
│   5. Reason:  "A100 is better for large models"     │
│   6. Act:     rent_compute(node="A100-node")        │
│   7. Observe: "GPU rented, SSH command provided"     │
│   8. Reason:  "Now I need to connect"               │
│   9. Act:     ssh_connect(host=..., user=...)       │
│   10. ...continues until task complete              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 5. Tool Schema & Validation

```
Tool Definition:
┌─────────────────────────────────────────┐
│ class RemoteWriteFileAction:            │
│   name = "remote_write_file"            │
│   description = "This tool will..."     │
│   args_schema = RemoteWriteFileInput    │
│   func = write_remote_file              │
└─────────────────────────────────────────┘
                    │
                    ↓
Pydantic Schema:
┌─────────────────────────────────────────┐
│ class RemoteWriteFileInput(BaseModel):  │
│   file_path: str = Field(...)           │
│   content: str = Field(...)             │
│   append: bool = Field(default=False)   │
└─────────────────────────────────────────┘
                    │
                    ↓
When Agent Calls:
┌─────────────────────────────────────────┐
│ tool_call = {                           │
│   "name": "remote_write_file",          │
│   "args": {                             │
│     "file_path": "test.py",             │
│     "content": "print('hello')"         │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
                    │
                    ↓
LangChain Validates:
┌─────────────────────────────────────────┐
│ 1. Parse args with Pydantic             │
│ 2. If valid: Execute function           │
│ 3. If invalid: Return error to agent    │
└─────────────────────────────────────────┘
```

## 6. Memory/State Management

```
Thread State Over Time:
┌─────────────────────────────────────────────────────┐
│ Message History (stored in MemorySaver)              │
├─────────────────────────────────────────────────────┤
│                                                      │
│ [0] HumanMessage("Check available GPUs")            │
│                                                      │
│ [1] AIMessage(                                      │
│       content="I'll check available GPUs",          │
│       tool_calls=[{name: "get_available_gpus"}]     │
│     )                                               │
│                                                      │
│ [2] ToolMessage(                                     │
│       content='{"gpus": [...]}',                    │
│       tool_call_id="call_123"                       │
│     )                                               │
│                                                      │
│ [3] AIMessage("I found 2 GPUs available...")        │
│                                                      │
│ [4] HumanMessage("Rent the A100")                   │
│                                                      │
│ [5] AIMessage(                                      │
│       content="I'll rent the A100",                 │
│       tool_calls=[{name: "rent_compute", ...}]      │
│     )                                               │
│                                                      │
│ ... conversation continues ...                       │
│                                                      │
│ Agent has access to FULL history for context        │
└─────────────────────────────────────────────────────┘
```

## 7. Error Flow

```
Error Handling Path:
┌─────────────────────────────────────────┐
│ Agent Calls Tool                         │
│ remote_write_file(file_path="test.py")   │
│         (missing content!)               │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ LangChain Validation                     │
│ ❌ ValidationError: content required     │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ Error Returned to Agent                  │
│ "Error: 1 validation error..."           │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ Agent Sees Error & Retries               │
│ "Let me fix that - I need to provide    │
│  the content parameter"                  │
│                                          │
│ remote_write_file(                       │
│   file_path="test.py",                   │
│   content="print('hello')"               │  
│ )                                        │
└─────────────────────────────────────────┘
```

## 8. Complete System Flow

```
     USER                    LANGCHAIN                    CLAUDE
      │                         │                           │
      │  "Train a model"        │                           │
      ├────────────────────────>│                           │
      │                         │                           │
      │                         │  Context + Tools + Msg    │
      │                         ├─────────────────────────->│
      │                         │                           │
      │                         │  "I'll help train..."     │
      │                         │  + tool_calls             │
      │                         │<──────────────────────────┤
      │                         │                           │
      │                         ├─> Execute get_gpus()      │
      │                         │                           │
      │                         │   Tool Result             │
      │                         ├─────────────────────────->│
      │                         │                           │
      │                         │  "Found A100 & V100..."   │
      │                         │  + tool_calls             │
      │                         │<──────────────────────────┤
      │                         │                           │
      │                         ├─> Execute rent_compute()  │
      │                         │                           │
      │                         │   ... continues ...       │
      │                         │                           │
      │  "I've set up your      │                           │
      │   training environment" │                           │
      │<────────────────────────┤                           │
      │                         │                           │
```

These diagrams show the complete flow from user input through LangChain orchestration to tool execution and back!