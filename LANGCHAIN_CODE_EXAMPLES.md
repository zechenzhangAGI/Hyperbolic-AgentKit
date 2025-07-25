# LangChain Code Examples - Step by Step

## Example 1: Simple Tool Call

Let's trace exactly what happens when the agent uses a tool:

### User Input
```python
user_message = "What files are in the current directory?"
```

### What the Agent Sees
```python
# The agent receives this context:
{
    "messages": [
        SystemMessage(content="""
            You are Dr. Nova, an AI Research Scientist...
            [character description]
        """),
        HumanMessage(content="What files are in the current directory?")
    ],
    "tools": [
        {
            "name": "remote_list_directory",
            "description": "This tool will list contents of a directory...",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."}
                }
            }
        },
        # ... other tools
    ]
}
```

### Agent's Response
```python
# Claude outputs:
AIMessage(
    content="I'll list the files in the current directory for you.",
    tool_calls=[
        {
            "id": "call_abc123",
            "name": "remote_list_directory",
            "args": {"path": "."}
        }
    ]
)
```

### LangChain Executes Tool
```python
# LangChain internally:
tool = get_tool_by_name("remote_list_directory")
result = tool.invoke({"path": "."})

# Which calls:
list_remote_directory(path=".")

# Returns:
"""
Directory: .
-rw-r--r--  [FILE] train.py (1234 bytes)
-rw-r--r--  [FILE] model.py (5678 bytes)
drwxr-xr-x  [DIR]  data
drwxr-xr-x  [DIR]  logs
"""
```

### Final Response to User
```python
# Agent sees the tool result and responds:
AIMessage(
    content="""I found the following files and directories in the current directory:

**Files:**
- `train.py` (1,234 bytes) - Likely your training script
- `model.py` (5,678 bytes) - Model definition

**Directories:**
- `data/` - Data directory
- `logs/` - Logs directory

Would you like me to look at any of these files or explore the subdirectories?"""
)
```

## Example 2: Multi-Step Task

### User Input
```python
"Create and run a simple PyTorch training script"
```

### Step 1: Agent Plans
```python
# Agent's internal reasoning:
"""
To create and run a PyTorch training script, I need to:
1. First create the script file
2. Then execute it
3. Check for any errors
"""
```

### Step 2: Create File
```python
# Tool call 1:
AIMessage(
    content="I'll create a simple PyTorch training script for you.",
    tool_calls=[{
        "name": "remote_write_file",
        "args": {
            "file_path": "simple_train.py",
            "content": '''import torch
import torch.nn as nn
import torch.optim as optim

# Simple model
class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 1)
    
    def forward(self, x):
        return self.fc(x)

# Training setup
model = SimpleNet()
optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.MSELoss()

# Dummy data
X = torch.randn(100, 10)
y = torch.randn(100, 1)

# Training loop
for epoch in range(10):
    optimizer.zero_grad()
    output = model(X)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()
    
    print(f'Epoch {epoch+1}, Loss: {loss.item():.4f}')

print("Training complete!")
'''
        }
    }]
)
```

### Step 3: Run Script
```python
# Tool call 2:
AIMessage(
    content="Now let me run the training script.",
    tool_calls=[{
        "name": "remote_shell",
        "args": {
            "command": "python simple_train.py"
        }
    }]
)
```

### Step 4: Handle Results
```python
# If successful:
ToolMessage(content="""
Epoch 1, Loss: 1.0234
Epoch 2, Loss: 0.9123
Epoch 3, Loss: 0.8234
...
Epoch 10, Loss: 0.5123
Training complete!
""")

# Agent's final response:
AIMessage(content="""
Great! I've successfully created and run a simple PyTorch training script. The training completed successfully with the loss decreasing from 1.0234 to 0.5123 over 10 epochs.

The script demonstrates:
- A simple linear neural network
- Adam optimizer setup
- MSE loss for regression
- Basic training loop with gradient updates

Would you like me to:
1. Modify the script to add more features (validation, checkpointing)?
2. Create a more complex model?
3. Add data loading from files?
""")
```

## Example 3: Error Handling

### When Things Go Wrong
```python
# User: "Run my training script"
# Agent tries:
tool_calls=[{
    "name": "remote_shell",
    "args": {"command": "python train.py"}
}]

# Error result:
ToolMessage(content="""
Traceback (most recent call last):
  File "train.py", line 1, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
""")

# Agent recognizes the error and fixes it:
AIMessage(
    content="I see PyTorch isn't installed. Let me install it first.",
    tool_calls=[{
        "name": "remote_shell",
        "args": {"command": "pip install torch torchvision"}
    }]
)
```

## Example 4: Complex Workflow

### GPU Rental and Setup
```python
# User: "I need to train a large model, can you set up a GPU for me?"

# Step 1: Check GPUs
agent.tool_calls = [{
    "name": "get_available_gpus",
    "args": {}
}]

# Result: List of available GPUs

# Step 2: Rent GPU
agent.tool_calls = [{
    "name": "rent_compute",
    "args": {
        "cluster_name": "us-west-2",
        "node_name": "node-a100-123",
        "gpu_count": "1"
    }
}]

# Result: GPU rental info with SSH details

# Step 3: Connect
agent.tool_calls = [{
    "name": "ssh_connect",
    "args": {
        "host": "123.45.67.89",
        "username": "ubuntu",
        "port": 22
    }
}]

# Step 4: Setup environment
agent.tool_calls = [{
    "name": "remote_shell",
    "args": {"command": "nvidia-smi"}  # Check GPU
}]

# Step 5: Create training script
agent.tool_calls = [{
    "name": "remote_write_file",
    "args": {
        "file_path": "train_large_model.py",
        "content": "... full training script ..."
    }
}]

# Step 6: Run training
agent.tool_calls = [{
    "name": "remote_shell",
    "args": {"command": "python train_large_model.py"}
}]
```

## How the Agent Decides Which Tool to Use

### Pattern Matching
```python
# User says: "Show me what's in the logs folder"
# Agent thinks:
# - "show me" → need to display/list
# - "what's in" → directory contents
# - "logs folder" → specific path
# Decision: Use remote_list_directory with path="logs"

# User says: "Create a config file with these settings"
# Agent thinks:
# - "create" → need to write
# - "file" → file operation
# - "with these settings" → has content
# Decision: Use remote_write_file

# User says: "Install numpy and pandas"
# Agent thinks:
# - "install" → package operation
# - "numpy and pandas" → Python packages
# Decision: Use remote_shell with "pip install numpy pandas"
```

## Behind the Scenes: Tool Registration

### How Tools Get into the System
```python
# 1. Define a tool class
class RemoteShellAction(HyperbolicAction):
    name = "remote_shell"
    description = "This tool will execute shell commands..."
    args_schema = RemoteShellInput
    func = execute_remote_command

# 2. Auto-discovery finds it
def get_all_hyperbolic_actions():
    return [cls() for cls in HyperbolicAction.__subclasses__()]

# 3. Convert to LangChain tool
langchain_tool = Tool(
    name=action.name,
    description=action.description,
    func=action.func,
    args_schema=action.args_schema
)

# 4. Agent receives list of all tools
agent = create_react_agent(
    llm=claude,
    tools=[langchain_tool1, langchain_tool2, ...],
    ...
)
```

## Debugging: See What's Actually Happening

### Enable Debug Mode
```python
# Add this to see ALL LangChain operations:
import langchain
langchain.debug = True

# Now when you run:
agent.invoke({"messages": [HumanMessage("List files")]})

# You'll see:
"""
[chain/start] [1:chain:AgentExecutor] Entering Chain run
[llm/start] [1:llm:ChatAnthropic] Entering LLM run
[llm/end] [1:llm:ChatAnthropic] Exiting LLM run
[tool/start] [1:tool:remote_list_directory] Entering Tool run
[tool/end] [1:tool:remote_list_directory] Exiting Tool run
[chain/end] [1:chain:AgentExecutor] Exiting Chain run
"""
```

### Inspect Tool Calls
```python
# In your code, add logging:
for chunk in agent.stream({"messages": [msg]}, config):
    if "agent" in chunk:
        for message in chunk["agent"]["messages"]:
            if hasattr(message, "tool_calls"):
                print(f"🔧 Tool calls: {message.tool_calls}")
    
    if "tools" in chunk:
        for message in chunk["tools"]["messages"]:
            print(f"📊 Tool result: {message.content[:100]}...")
```

## Key Takeaways

1. **LangChain is the Orchestrator**: It manages the flow between user → LLM → tools → response
2. **Tools are Just Functions**: With metadata (name, description, schema)
3. **The Agent Decides**: Based on context and available tools
4. **Everything is a Message**: HumanMessage, AIMessage, ToolMessage
5. **State is Preserved**: Full conversation history is available

This is how your chatbot really works under the hood!