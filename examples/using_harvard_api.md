# Using Harvard's Custom OpenAI API

This guide shows how to use Harvard's custom OpenAI endpoint with the Hyperbolic AgentKit.

## Configuration

### 1. Set Environment Variables

Add to your `.env` file:

```bash
# Harvard API Configuration
HARVARD_API_KEY=709KLfil8udIORZu9UjjE4jhaGTG6uW0
LLM_PROVIDER=harvard
LLM_MODEL=o3-mini-2025-01-31  # or gpt-4.1-mini-2025-04-14
```

### 2. Available Harvard Models

- `o3-mini-2025-01-31` - Harvard's o3-mini model
- `gpt-4.1-mini-2025-04-14` - Harvard's GPT-4.1 mini model

## Usage Examples

### Command Line

```bash
# Set Harvard as default provider
export LLM_PROVIDER=harvard
export LLM_MODEL=o3-mini-2025-01-31
export HARVARD_API_KEY=your_api_key

# Run the chatbot
poetry run python chatbot.py
```

### Runtime Switching

```
You: /model harvard o3-mini-2025-01-31
Switched to harvard with model o3-mini-2025-01-31

You: /model harvard-o3-mini
Switched to harvard with model o3-mini-2025-01-31 (using alias)

You: Solve this complex reasoning problem...
Dr. Nova (via Harvard o3-mini): [Response using Harvard's o3-mini model]
```

## Technical Details

### API Endpoint
- Base URL: `https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1`
- Authentication: Uses `api-key` header instead of standard `Authorization` header

### Model Parameters
- Temperature: Fixed at 1.0 (as per Harvard's configuration)
- No streaming support (standard request-response)

### Rate Limiting
The implementation includes:
- Automatic retries with exponential backoff
- Maximum 3 retry attempts
- 60-second timeout per request

## Comparison with Standard OpenAI

| Feature | Standard OpenAI | Harvard Endpoint |
|---------|----------------|------------------|
| Auth Header | `Authorization: Bearer` | `api-key` |
| Models | Public models | Harvard-specific |
| Temperature | Configurable | Fixed at 1.0 |
| Endpoint | api.openai.com | Harvard's custom URL |

## Example Code

If you want to use Harvard's API directly in your code:

```python
from base_utils.llm_factory import LLMFactory

# Create Harvard LLM instance
llm = LLMFactory.create_llm(
    provider="harvard",
    model="o3-mini-2025-01-31"
)

# Use with LangChain
from langchain_core.messages import HumanMessage

response = llm.invoke([
    HumanMessage(content="Explain quantum computing")
])
print(response.content)
```

## Troubleshooting

1. **API Key Error**: Ensure `HARVARD_API_KEY` is set in your `.env` file
2. **Model Not Found**: Use exact model names (no aliases internally)
3. **Connection Issues**: Check if you're on Harvard network or have proper access
4. **Rate Limits**: The API may have usage limits - check with Harvard IT

## Security Notes

- Never commit API keys to version control
- The Harvard API key should be kept confidential
- Use environment variables for all sensitive configuration