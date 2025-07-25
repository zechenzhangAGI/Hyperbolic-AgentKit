# Coinbase Tools Conditional Initialization

**Date**: 2025-07-24
**Author**: Claude (AI Assistant)
**Status**: Implemented

## Overview

Made Coinbase AgentKit initialization fully conditional based on the `USE_COINBASE_TOOLS` environment variable. This allows users to run the agent without Coinbase dependencies when not needed.

## Changes Made

### 1. **Conditional Imports**
- Moved Coinbase imports from top-level to conditional blocks
- Only import when `USE_COINBASE_TOOLS=true`
- Prevents unnecessary dependencies

### 2. **Conditional Initialization**
```python
# Before: Always initialized
agent_kit = AgentKit(AgentKitConfig(...))

# After: Only when enabled
if os.getenv("USE_COINBASE_TOOLS", "true").lower() == "true":
    from coinbase_agentkit import ...
    agent_kit = AgentKit(AgentKitConfig(...))
else:
    agent_kit = None
```

### 3. **Tool Registration**
- Updated `create_agent_tools` to handle `agent_kit=None`
- Only adds Coinbase tools when agent_kit is available

## Benefits

1. **Reduced Dependencies**: Users who don't need blockchain features don't need Coinbase SDK
2. **Faster Startup**: Skips Coinbase initialization when not needed
3. **Cleaner Logs**: No Coinbase-related messages when disabled
4. **Better Modularity**: Each feature set can be toggled independently

## Usage

### To Disable Coinbase Tools:
```bash
# In .env
USE_COINBASE_TOOLS=false
```

### To Enable Coinbase Tools:
```bash
# In .env
USE_COINBASE_TOOLS=true
CDP_API_KEY_NAME=your_key_name
CDP_API_KEY_PRIVATE=your_private_key
```

## Testing

Created comprehensive tests to verify:
- Agent works without Coinbase tools
- No Coinbase modules imported when disabled
- Other tools (Hyperbolic, browser, etc.) work normally
- No errors with `agent_kit=None`

## Note on link_wallet_address

The `link_wallet_address` tool is part of Hyperbolic tools, not Coinbase. It allows linking a wallet to the Hyperbolic account for GPU payments.