# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Set up Python environment (requires Python 3.12)
poetry env use python3.12
poetry install

# Install Playwright browsers (required for browser automation)
poetry run playwright install
```

### Running the Application
```bash
# Terminal Interface (main chatbot)
poetry run python chatbot.py

# Voice Agent (requires OpenAI API key)
PYTHONPATH=$PWD/server/src poetry run python server/src/server/app.py

# Gradio Web Interface
poetry run python gradio_ui.py
```

### YouTube Scraper Commands
```bash
# Run YouTube scraper
cd youtube_scraper
poetry run python main.py

# Process videos in parallel
poetry run python main.py --parallel --max-workers 3

# Database utilities
poetry run python db_utilities.py stats
poetry run python db_utilities.py list
poetry run python db_utilities.py reset
```

## High-Level Architecture

### Core Components

1. **Agent Framework**
   - `chatbot.py`: Main agent initialization and orchestration
   - Character-based personalities loaded from JSON files in `characters/`
   - LangChain-based ReAct agent with Claude 3.5 Sonnet as the LLM
   - Memory persistence using LangGraph's MemorySaver

2. **Tool Registration Flow**
   - Tools are registered in two places:
     - `chatbot.py`: `create_agent_tools()` function for the terminal/Gradio interface
     - `server/src/server/tools.py`: `create_tools()` function for the voice agent
   - Environment variables control which tools are enabled (see `.env.example`)
   - Tools are conditionally loaded based on configuration

3. **Agent-Specific Capabilities**
   Each capability is organized in its own directory:
   - `hyperbolic_agentkit_core/`: GPU compute operations (rent, terminate, SSH access)
   - `twitter_agent/`: Twitter API integration with knowledge base
   - `browser_agent/`: Browser automation using Playwright
   - `podcast_agent/`: Video processing and transcription
   - `writing_agent/`: AI-powered content generation with research
   - `github_agent/`: GitHub API interactions
   - `youtube_scraper/`: Automated YouTube content collection

4. **Knowledge Base Systems**
   - **Twitter Knowledge Base**: Vector database of KOL tweets for informed posting
   - **Podcast Knowledge Base**: Searchable transcripts for accurate Q&A
   - Both use ChromaDB with sentence-transformers for embeddings

5. **Voice Agent Architecture**
   - WebSocket-based real-time communication
   - Located in `server/src/server/`
   - Uses OpenAI's realtime voice API (gpt-4o-realtime-preview)
   - Shares character configurations with main agent

6. **External Integrations**
   - **Coinbase CDP**: Blockchain operations (wallets, tokens, transactions)
   - **Hyperbolic**: GPU compute marketplace integration
   - **Twitter/X**: Full API integration for social media operations
   - **Tavily**: Web search for research and fact-checking

### Key Design Patterns

1. **Tool Creation**: Tools are created as LangChain Tool objects with descriptions
2. **State Management**: Twitter state tracks mentions and interactions to prevent duplicates
3. **Character System**: JSON-based character definitions control agent personality
4. **Modular Architecture**: Each agent capability is self-contained in its own directory
5. **Environment-Based Configuration**: Features are toggled via environment variables

### Development Notes

- Always check environment variables in `.env` before adding new tools
- Character files in `characters/` define agent personalities and behaviors
- Tools must be registered in both `chatbot.py` and `server/tools.py` if needed in both interfaces
- Knowledge bases require initialization before first use
- SSH access for GPU compute requires RSA keys (not ed25519)