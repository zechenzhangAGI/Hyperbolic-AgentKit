# Harvard API - Complete Integration Guide

## 🎉 Great News: Harvard API Supports Tool Calling!

After thorough testing, we've confirmed that Harvard's OpenAI-compatible API **fully supports tool/function calling**. This means you can use Harvard models with ALL features of the Hyperbolic AgentKit, including:

- ✅ Browser automation
- ✅ File operations
- ✅ GPU compute management
- ✅ ReAct agents
- ✅ Multi-step reasoning
- ✅ All other tools!

## Quick Start

1. **Set your API key in `.env`:**
```bash
HARVARD_API_KEY=your_harvard_api_key
LLM_PROVIDER=harvard
LLM_MODEL=o3-mini-2025-01-31
```

2. **Run the chatbot:**
```bash
poetry run python chatbot.py
```

3. **Use any tools:**
```
You: Rent a GPU and create a training script
Dr. Nova: [Uses get_available_gpus, rent_compute, ssh_connect, remote_write_file tools]
```

## Available Models

Harvard provides access to many models including:

### Reasoning Models
- `o3-mini-2025-01-31` - Latest o3-mini with tool support
- `o3` - Full o3 model
- `o1-preview` - o1 preview model

### GPT Models  
- `gpt-4.1-mini-2025-04-14` - GPT-4.1 mini
- `gpt-4o` - GPT-4 optimized
- `gpt-4` - Standard GPT-4

### Research Models
- `o3-deep-research` - Deep research model
- `o4-mini-deep-research` - Mini research model

## Technical Details

### Authentication
Harvard requires both headers:
- `Authorization: Bearer <api_key>` (standard OpenAI)
- `api-key: <api_key>` (Harvard-specific)

Our integration handles this automatically.

### Tool Calling Format
Harvard supports both formats:
- Modern `tools` parameter (recommended)
- Legacy `functions` parameter

Example tool response:
```json
{
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function", 
      "function": {
        "name": "calculate",
        "arguments": "{\"expression\": \"42 * 37\"}"
      }
    }
  ]
}
```

## Usage Examples

### With Tools
```python
# The agent can use all tools
You: Search for machine learning papers and summarize them
Dr. Nova: I'll search for recent ML papers...
[Uses web_search tool]
[Uses get_info tool]
Here's a summary of recent developments...

You: Create a PyTorch training script on a GPU
Dr. Nova: I'll rent a GPU and set up the script...
[Uses get_available_gpus]
[Uses rent_compute]
[Uses ssh_connect]
[Uses remote_write_file]
[Uses remote_shell]
```

### Model Switching
```bash
# Switch between Harvard models
/model harvard o3-mini-2025-01-31
/model harvard gpt-4.1-mini-2025-04-14
/model harvard o1-preview

# Or use other providers when needed
/model anthropic claude-sonnet-4
/model openai gpt-4
```

## Cost Tracking

Harvard API includes credit usage in responses:
```json
{
  "your_harvard_credits_used_this_transaction": 0.00047,
  "your_harvard_credits_still_available": 499.9878
}
```

## Performance Tips

1. **o3-mini** is fast and supports tools well
2. **gpt-4.1-mini** is good for general tasks
3. **o3-deep-research** for complex reasoning (but slower)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check API key in .env |
| Model not found | Use exact model name from /models |
| Tool calls failing | Ensure you're using a model that supports tools |
| Slow responses | Normal for reasoning models, be patient |

## Summary

Harvard's API is a **full-featured OpenAI-compatible endpoint** that supports:
- ✅ All chat completions features
- ✅ Tool/function calling
- ✅ System messages
- ✅ Multi-turn conversations
- ✅ Streaming (if needed)
- ✅ Embeddings endpoint
- ✅ Many model choices

You can use it as a drop-in replacement for OpenAI API with the added benefit of Harvard-specific models and credit tracking!