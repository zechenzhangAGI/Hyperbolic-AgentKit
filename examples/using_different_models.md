# Using Different LLM Models

This guide shows how to use different LLM providers and models with the Hyperbolic AgentKit.

## Configuration Methods

### 1. Environment Variables (Default)

Set in your `.env` file:

```bash
# Use OpenAI's o3 model
LLM_PROVIDER=openai
LLM_MODEL=o3

# Use Anthropic's Claude Sonnet 4
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514

# Use Google's Gemini
LLM_PROVIDER=google
LLM_MODEL=gemini-pro
```

### 2. Runtime Switching

While the chatbot is running, use the `/model` command:

```
You: /model
Current LLM Configuration:
  Provider: anthropic
  Model: claude-sonnet-4-20250514

You: /model openai o3
Switched to openai with model o3

You: /model gpt-4
Switched to openai with model gpt-4 (using alias)
```

## Available Models

### Anthropic
- `claude-3-opus-20240229` (alias: `claude-opus`)
- `claude-3-sonnet-20240229` (alias: `claude-sonnet`)
- `claude-3-haiku-20240307` (alias: `claude-haiku`)
- `claude-sonnet-4-20250514` (alias: `claude-sonnet-4`)

### OpenAI
- `gpt-4` 
- `gpt-4-turbo-preview` (alias: `gpt-4-turbo`)
- `gpt-3.5-turbo` (alias: `gpt-3.5`)
- `o1-preview` (alias: `o1`)
- `o1-mini`
- `o3` (when available)
- `o3-mini` (when available)

### Google
- `gemini-pro` (alias: `gemini`)
- `gemini-pro-vision` (alias: `gemini-vision`)

### Ollama (Local)
- `llama2`
- `mistral`
- `codellama`
- `mixtral`

## Example Usage

### Using OpenAI's o3 Model

1. Set environment variables:
```bash
export OPENAI_API_KEY=your_api_key
export LLM_PROVIDER=openai
export LLM_MODEL=o3
```

2. Run the chatbot:
```bash
poetry run python chatbot.py
```

3. Or switch during runtime:
```
You: /model openai o3
Switched to openai with model o3

You: Create a complex reasoning task
Dr. Nova (via o3): [Response using o3's advanced reasoning capabilities]
```

### Using Local Models with Ollama

1. Install and start Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Start Ollama server (usually auto-starts)
ollama serve
```

2. Configure the agent:
```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=llama2
export OLLAMA_BASE_URL=http://localhost:11434
```

## Important Notes

1. **API Keys**: Each provider requires its own API key in the `.env` file
2. **Model Availability**: Some models (like o3) may have limited availability
3. **Feature Support**: Not all models support all features (e.g., o1/o3 have fixed temperature)
4. **Cost**: Different models have different pricing - check provider documentation
5. **Performance**: Local models (Ollama) don't require internet but may be slower

## Troubleshooting

If you get an error when switching models:

1. Check API key is set for the provider
2. Verify model name is correct
3. Ensure you have access to the model (some require waitlist)
4. Check provider-specific requirements (e.g., Ollama server running)

Example error handling:
```
You: /model openai o3
Error: OPENAI_API_KEY not found in environment

You: /model openai invalid-model
Error: Model 'invalid-model' is not available for provider 'openai'
Available models for openai: gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo, o1-preview, o1-mini, o3, o3-mini
```