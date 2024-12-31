import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import json
from typing import List, Dict, Any
import random


# Load environment variables from .env file
load_dotenv(override=True)

# Add the parent directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import SKLearnVectorStore
from langchain.tools import Tool

# Import CDP related modules
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from cdp_langchain.tools import CdpTool
from pydantic import BaseModel, Field
from cdp import Wallet

# Import Hyperbolic related modules
from hyperbolic_langchain.agent_toolkits import HyperbolicToolkit
from hyperbolic_langchain.utils import HyperbolicAgentkitWrapper
from twitter_langchain import TwitterApiWrapper, TwitterToolkit
from custom_twitter_actions import create_delete_tweet_tool

# Import local modules
from utils import (
    Colors, 
    print_ai, 
    print_system, 
    print_error, 
    ProgressIndicator, 
    run_with_progress, 
    format_ai_message_content
)
from twitter_state import TwitterState, MENTION_CHECK_INTERVAL, MAX_MENTIONS_PER_INTERVAL

# Constants
ALLOW_DANGEROUS_REQUEST = True  # Set to False in production for security
wallet_data_file = "wallet_data.txt"

MENTION_CHECK_INTERVAL = 60 * 15 # 15 minutes

# Create TwitterState instance
twitter_state = TwitterState()

# Create tools for Twitter state management
check_replied_tool = Tool(
    name="has_replied_to",
    func=twitter_state.has_replied_to,
    description="Check if we have already replied to a tweet. Input should be a tweet ID string."
)

add_replied_tool = Tool(
    name="add_replied_to",
    func=twitter_state.add_replied_tweet,
    description="Add a tweet ID to the database of replied tweets."
)

# Knowledge base setup
urls = [
    "https://docs.prylabs.network/docs/monitoring/checking-status",
]

# Load and process documents
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=1000, chunk_overlap=200
)
doc_splits = text_splitter.split_documents(docs_list)

vectorstore = SKLearnVectorStore.from_documents(
    documents=doc_splits,
    embedding=NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local"),
)

retriever = vectorstore.as_retriever(k=3)

retrieval_tool = Tool(
    name="retrieval_tool",
    description="Useful for retrieving information from the knowledge base about running Ethereum operations.",
    func=retriever.get_relevant_documents
)

# Multi-token deployment setup
DEPLOY_MULTITOKEN_PROMPT = """
This tool deploys a new multi-token contract with a specified base URI for token metadata.
The base URI should be a template URL containing {id} which will be replaced with the token ID.
For example: 'https://example.com/metadata/{id}.json'
"""

class DeployMultiTokenInput(BaseModel):
    """Input argument schema for deploy multi-token contract action."""
    base_uri: str = Field(
        ...,
        description="The base URI template for token metadata. Must contain {id} placeholder.",
        example="https://example.com/metadata/{id}.json"
    )

def deploy_multi_token(wallet: Wallet, base_uri: str) -> str:
    """Deploy a new multi-token contract with the specified base URI."""
    if "{id}" not in base_uri:
        raise ValueError("base_uri must contain {id} placeholder")
    
    deployed_contract = wallet.deploy_multi_token(base_uri)
    result = deployed_contract.wait()
    return f"Successfully deployed multi-token contract at address: {result.contract_address}"

def loadCharacters(charactersArg: str) -> List[Dict[str, Any]]:
    """Load character files and return their configurations."""
    characterPaths = charactersArg.split(",") if charactersArg else []
    loadedCharacters = []

    if not characterPaths:
        # Load default chainyoda character
        default_path = os.path.join(os.path.dirname(__file__), "characters/chainyoda.json")
        characterPaths.append(default_path)

    for characterPath in characterPaths:
        try:
            # Search in common locations
            searchPaths = [
                characterPath,
                os.path.join("characters", characterPath),
                os.path.join(os.path.dirname(__file__), "characters", characterPath)
            ]

            for path in searchPaths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        character = json.load(f)
                        loadedCharacters.append(character)
                        print(f"Successfully loaded character from: {path}")
                        break
            else:
                raise FileNotFoundError(f"Could not find character file: {characterPath}")

        except Exception as e:
            print(f"Error loading character from {characterPath}: {e}")
            raise

    return loadedCharacters

def process_character_config(character: Dict[str, Any]) -> str:
    """Process character configuration into agent personality."""
    
    # Format bio and lore
    bio = "\n".join([f"- {item}" for item in character.get('bio', [])])
    lore = "\n".join([f"- {item}" for item in character.get('lore', [])])
    knowledge = "\n".join([f"- {item}" for item in character.get('knowledge', [])])
    
    # Format style guidelines
    style_all = "\n".join([f"- {item}" for item in character.get('style', {}).get('all', [])])
    # style_chat = "\n".join([f"- {item}" for item in character.get('style', {}).get('chat', [])])
    # style_post = "\n".join([f"- {item}" for item in character.get('style', {}).get('post', [])])

    # Randomly select 10 post examples
    all_posts = character.get('postExamples', [])
    selected_posts = random.sample(all_posts, min(15, len(all_posts)))
    
    post_examples = "\n".join([
        f"Example {i+1}: {post}"
        for i, post in enumerate(selected_posts)
        if isinstance(post, str) and post.strip()
    ])
    
    # Compile personality prompt
    personality = f"""You are {character['name']}, with the following characteristics:

    BIO:
    {bio}

    LORE:
    {lore}

    KNOWLEDGE:
    {knowledge}

    POST EXAMPLES:
    {post_examples}

    STYLE GUIDELINES:
    {style_all}

    CORE CAPABILITIES:

    1. Blockchain Operations (via CDP):
    - Interact onchain via Coinbase Developer Platform
    - Deploy your own tokens and manage your wallets
    - Request funds from faucet on network ID `base-sepolia`

    2. Compute Operations (via Hyperbolic):
    - Rent compute resources
    - Check your GPU status and availability
    - Connect to your remote servers via SSH (use ssh_connect)
    - Execute commands on remote server (use remote_shell)

    3. System Operations:
    - Use 'ssh_status' to check current SSH connection
    - Search the internet for current information
    - Post your updates on X (Twitter)
    - Monitor and respond to mentions
    - Track replied tweets in database

    4. Knowledge Base Access:
    - Always use the DuckDuckGoSearchRun web_search tool for current information, never make it up. If you are asked about current information, and you hit a rate limit on web_search, do not reply and instead wait till the next mention check.
    - Query Ethereum operations documentation
    - Access real-time blockchain information
    - Retrieve relevant technical documentation

    Remember to:
    1. Stay in character at all times
    2. Use your knowledge and capabilities appropriately
    3. Maintain consistent personality traits
    4. Follow style guidelines for all communications
    5. Use tools and capabilities when needed
    6. Do not reply to mentions that seem to be spam or bots
    7. All tweets MUST be less than 280 characters

    When using tools:
    1. Check if you've replied to tweets using has_replied_to
    2. Track replied tweets using add_replied_to
    3. Use retrieval_tool for Ethereum documentation
    
    """

    print_system(personality)

    return personality

def initialize_agent():
    """Initialize the agent with CDP Agentkit and Hyperbolic Agentkit."""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

    try:
        characters = loadCharacters(os.getenv("CHARACTER_FILE", "chainyoda.json"))
        character = characters[0]  # Use first character if multiple loaded
    except Exception as e:
        print_error(f"Error loading character: {e}")
        sys.exit(1)

            # Process character configuration
    personality = process_character_config(character)

    wallet_data = None
    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    # Configure CDP Agentkit
    values = {}
    if wallet_data is not None:
        values = {"cdp_wallet_data": wallet_data}
    
    agentkit = CdpAgentkitWrapper(**values)
    
    # Save wallet data
    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    # Initialize toolkits and get tools
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()

    hyperbolic_agentkit = HyperbolicAgentkitWrapper()
    hyperbolic_toolkit = HyperbolicToolkit.from_hyperbolic_agentkit_wrapper(hyperbolic_agentkit)
    tools.extend(hyperbolic_toolkit.get_tools())

    twitter_api_wrapper = TwitterApiWrapper()
    twitter_toolkit = TwitterToolkit.from_twitter_api_wrapper(twitter_api_wrapper)
    tools.extend(twitter_toolkit.get_tools())

    # Create deploy multi-token tool
    deployMultiTokenTool = CdpTool(
        name="deploy_multi_token",
        description=DEPLOY_MULTITOKEN_PROMPT,
        cdp_agentkit_wrapper=agentkit,
        args_schema=DeployMultiTokenInput,
        func=deploy_multi_token,
    )

    # Add additional tools
    tools.extend([
        deployMultiTokenTool,
        DuckDuckGoSearchRun(
            name="web_search",
            description="Search the internet for current information."
        ),
        check_replied_tool,
        add_replied_tool,
        retrieval_tool
    ])

        # Add our custom delete tweet tool
    delete_tweet_tool = create_delete_tweet_tool(twitter_api_wrapper)
    tools.append(delete_tweet_tool)
    

    # Add request tools
    toolkit = RequestsToolkit(
        requests_wrapper=TextRequestsWrapper(headers={}),
        allow_dangerous_requests=ALLOW_DANGEROUS_REQUEST,
    )   
    tools.extend(toolkit.get_tools())

    # Configure memory and agent
    memory = MemorySaver()
    memory = MemorySaver()
    config = {
        "configurable": {
            "thread_id": f"{character['name']} Agent",
            "character": character["name"]
        },
        "character": {
            "name": character["name"],
            "bio": character.get("bio", []),
            "lore": character.get("lore", []),
            "knowledge": character.get("knowledge", []),
            "style": character.get("style", {}),
            "messageExamples": character.get("messageExamples", []),
            "postExamples": character.get("postExamples", [])
        }
    }

    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=personality,
    ), config


def choose_mode():
    """Choose whether to run in autonomous or chat mode."""
    while True:
        print("\nAvailable modes:")
        print("1. chat    - Interactive chat mode")
        print("2. auto    - Autonomous action mode")

        choice = input("\nChoose a mode (enter number or name): ").lower().strip()
        if choice in ["1", "chat"]:
            return "chat"
        elif choice in ["2", "auto"]:
            return "auto"
        print("Invalid choice. Please try again.")

def run_with_progress(func, *args, **kwargs):
    """Run a function while showing a progress indicator."""
    progress = ProgressIndicator()
    
    try:
        progress.start()
        generator = func(*args, **kwargs)
        chunks = []
        
        for chunk in generator:
            progress.stop()
            chunks.append(chunk)
            progress.start()
        
        return chunks
    finally:
        progress.stop()

def run_chat_mode(agent_executor, config):
    """Run the agent interactively based on user input."""
    print_system("Starting chat mode... Type 'exit' to end.")
    print_system("Commands:")
    print_system("  exit     - Exit the chat")
    print_system("  status   - Check if agent is responsive")
    
    while True:
        try:
            prompt = f"{Colors.BLUE}{Colors.BOLD}User: {Colors.ENDC}"
            user_input = input(prompt)
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                break
            elif user_input.lower() == "status":
                print_system("Agent is responsive and ready for commands.")
                continue
            
            print_system(f"\nStarted at: {datetime.now().strftime('%H:%M:%S')}")
            
            chunks = run_with_progress(
                agent_executor.stream,
                {"messages": [HumanMessage(content=user_input)]},
                config
            )
            
            # Process the returned chunks
            for chunk in chunks:
                if "agent" in chunk:
                    response = chunk["agent"]["messages"][0].content
                    print_ai(format_ai_message_content(response))
                elif "tools" in chunk:
                    print_system(chunk["tools"]["messages"][0].content)
                print_system("-------------------")
                
        except KeyboardInterrupt:
            print_system("\nExiting chat mode...")
            break
        except Exception as e:
            print_error(f"Error: {str(e)}")

def run_autonomous_mode(agent_executor, config):
    """Run the agent autonomously with specified intervals."""
    print_system(f"Starting autonomous mode as {config['character']['name']}...")
    twitter_state.load()
    progress = ProgressIndicator()

    while True:
        try:
            if not twitter_state.can_check_mentions():
                wait_time = MENTION_CHECK_INTERVAL - (datetime.now() - twitter_state.last_check_time).total_seconds()
                print_system(f"Waiting {int(wait_time)} seconds before next check...")
                time.sleep(wait_time)
                continue

            print_system("Checking for new mentions and creating new post...")
            progress.start()
            
            thought = f"""You are an AI-powered Twitter bot designed to create engaging posts and automatically scan for and reply to mentions using Twitter LangChain resources.
            Tweets can be up to 280 characters, but you should variate between one word, one sentence, and a few sentences.

            Goals:
            1. Create an engaging tweet that reflects your character's personality and knowledge
            2. Check for and reply to any new Twitter mentions
            
            Account ID to monitor: run the twitter_lanchain function account_details to get the account ID
            
            Current State (stored in SQLite database):
            - Last processed mention ID: {twitter_state.last_mention_id}
            - Only process mentions newer than this ID
            - All replied tweets are tracked in the SQLite database
            - IMPORTANT: After checking mentions, wait 15 minutes before checking again to respect API limits
            - Current time: {datetime.now().strftime('%H:%M:%S')}

            Before replying to any mention:
            1. Query the SQLite database to check if tweet_id exists using has_replied_to
            2. Only proceed with reply if has_replied_to returns False
            3. After successful reply, store the tweet_id in the database using add_replied_tweet

            Personality Guidelines:
            - Always stay in the personality of your character
            - Make sure your response is relevant to the tweet content
            - Be friendly, witty, and engaging in your responses
            - Share interesting insights or thought-provoking perspectives when relevant
            - Feel free to ask follow-up questions to encourage discussion
            - Always keep your tweets under 280 characters
            """

            chunks = run_with_progress(
                agent_executor.stream,
                {"messages": [HumanMessage(content=thought)]},
                config
            )
            
            progress.stop()

            # Process the returned chunks
            for chunk in chunks:
                if "agent" in chunk:
                    response = chunk["agent"]["messages"][0].content
                    print_ai(format_ai_message_content(response))
                    
                    # Handle tool responses
                    if isinstance(response, list):
                        for item in response:
                            if item.get('type') == 'tool_use' and item.get('name') == 'add_replied_to':
                                tweet_id = item['input'].get('__arg1')
                                if tweet_id:
                                    print_system(f"Adding tweet {tweet_id} to database...")
                                    result = twitter_state.add_replied_tweet(tweet_id)
                                    print_system(result)
                                    
                                    # Update state after successful reply
                                    twitter_state.last_mention_id = tweet_id
                                    twitter_state.last_check_time = datetime.now()
                                    twitter_state.save()
                
                elif "tools" in chunk:
                    print_system(chunk["tools"]["messages"][0].content)
                print_system("-------------------")

            print_system(f"Processed mentions. Waiting {MENTION_CHECK_INTERVAL/60} minutes before next check...")
            time.sleep(MENTION_CHECK_INTERVAL)

        except KeyboardInterrupt:
            progress.stop()
            print_system("Saving state and exiting...")
            twitter_state.save()
            sys.exit(0)
        except Exception as e:
            progress.stop()
            print_error(f"Error: {str(e)}")
            print_system("Continuing after error...")
            time.sleep(MENTION_CHECK_INTERVAL)

def main():
    """Start the chatbot agent."""
    try:
        agent_executor, config = initialize_agent()
        mode = choose_mode()
        
        if mode == "chat":
            run_chat_mode(agent_executor=agent_executor, config=config)
        elif mode == "auto":
            run_autonomous_mode(agent_executor=agent_executor, config=config)
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting Agent...")
    main()
