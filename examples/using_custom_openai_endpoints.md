# Using Custom OpenAI-Compatible Endpoints

This guide shows how to use any OpenAI-compatible API endpoint with the Hyperbolic AgentKit.

## Overview

Many providers offer OpenAI-compatible APIs:
- Local LLM servers (vLLM, FastChat, etc.)
- Cloud providers with OpenAI-compatible interfaces
- Corporate/institutional endpoints
- Custom deployments

## Configuration

### Basic Setup

Add to your `.env` file:

```bash
# Custom OpenAI-compatible endpoint
CUSTOM_OPENAI_API_KEY=your_api_key
CUSTOM_OPENAI_BASE_URL=https://your-endpoint.com/v1
LLM_PROVIDER=custom_openai
LLM_MODEL=your-model-name
```

### With Custom Headers

Some endpoints require additional headers:

```bash
CUSTOM_OPENAI_HEADERS={"X-Custom-Auth": "token123", "X-API-Version": "2.0"}
```

## Examples

### 1. Using vLLM Server

```bash
# vLLM configuration
CUSTOM_OPENAI_API_KEY=dummy  # vLLM often doesn't need auth
CUSTOM_OPENAI_BASE_URL=http://localhost:8000/v1
LLM_PROVIDER=custom_openai
LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
```

### 2. Using FastChat

```bash
# FastChat configuration
CUSTOM_OPENAI_API_KEY=dummy
CUSTOM_OPENAI_BASE_URL=http://localhost:8000/v1
LLM_PROVIDER=custom_openai
LLM_MODEL=vicuna-7b-v1.5
```

### 3. Using Perplexity AI

```bash
# Perplexity configuration
CUSTOM_OPENAI_API_KEY=pplx-xxxxxxxxxxxxx
CUSTOM_OPENAI_BASE_URL=https://api.perplexity.ai
LLM_PROVIDER=custom_openai
LLM_MODEL=mixtral-8x7b-instruct
```

### 4. Using Together AI

```bash
# Together AI configuration
CUSTOM_OPENAI_API_KEY=your_together_api_key
CUSTOM_OPENAI_BASE_URL=https://api.together.xyz/v1
LLM_PROVIDER=custom_openai
LLM_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
```

## Runtime Usage

```
You: /model custom_openai mixtral-8x7b
Switched to custom_openai with model mixtral-8x7b

You: Explain the theory of relativity
Dr. Nova (via Custom Endpoint): [Response from your custom model]
```

## Advanced Configuration

### Custom Headers Example

For endpoints requiring special authentication:

```python
# In your .env
CUSTOM_OPENAI_HEADERS={"X-API-Key": "special-key", "X-Org-ID": "org-123"}
```

### Programmatic Usage

```python
from base_utils.llm_factory import LLMFactory

# Create custom endpoint LLM
llm = LLMFactory.create_llm(
    provider="custom_openai",
    model="your-model",
    api_key="your-key",
    base_url="https://your-endpoint.com/v1",
    custom_headers={"X-Custom": "value"}
)

# Use with LangChain
response = llm.invoke([
    HumanMessage(content="Hello, how are you?")
])
```

## Common Endpoints

| Provider | Base URL | Notes |
|----------|----------|-------|
| vLLM | `http://localhost:8000/v1` | Local deployment |
| FastChat | `http://localhost:8000/v1` | Local deployment |
| Together AI | `https://api.together.xyz/v1` | Cloud service |
| Anyscale | `https://api.endpoints.anyscale.com/v1` | Cloud service |
| Perplexity | `https://api.perplexity.ai` | Cloud service |
| Deepinfra | `https://api.deepinfra.com/v1/openai` | Cloud service |

## Troubleshooting

### 1. Connection Refused
- Check if the server is running
- Verify the base URL and port
- Ensure firewall allows connection

### 2. Authentication Failed
- Verify API key format
- Check if custom headers are needed
- Some local servers don't need authentication (use "dummy" key)

### 3. Model Not Found
- List available models: `curl http://your-endpoint/v1/models`
- Use exact model name from the endpoint
- Some endpoints have specific model naming conventions

### 4. Timeout Issues
- Increase timeout in configuration
- Check if model is loaded on server
- Some models take time to initialize

## Testing Your Endpoint

Test with curl first:

```bash
curl http://your-endpoint/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "your-model",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Security Considerations

1. **Local Endpoints**: Ensure proper network isolation
2. **API Keys**: Never expose in public repositories
3. **HTTPS**: Use HTTPS for production endpoints
4. **Headers**: Sensitive headers should be in environment variables
5. **Firewall**: Restrict access to local endpoints