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
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_nomic.embeddings import NomicEmbeddings
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import WebBaseLoader
# from langchain_community.vectorstores import SKLearnVectorStore
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
from custom_twitter_actions import create_delete_tweet_tool, create_get_user_id_tool, create_get_user_tweets_tool

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

# # Knowledge base setup
# urls = [
#     "https://docs.prylabs.network/docs/monitoring/checking-status",
# ]

# # Load and process documents
# docs = [WebBaseLoader(url).load() for url in urls]
# docs_list = [item for sublist in docs for item in sublist]

# text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
#     chunk_size=1000, chunk_overlap=200
# )
# doc_splits = text_splitter.split_documents(docs_list)

# vectorstore = SKLearnVectorStore.from_documents(
#     documents=doc_splits,
#     embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
# )

# retriever = vectorstore.as_retriever(k=3)

# retrieval_tool = Tool(
#     name="retrieval_tool",
#     description="Useful for retrieving information from the knowledge base about running Ethereum operations.",
#     func=retriever.get_relevant_documents
# )

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

    topics = "\n".join([f"- {item}" for item in character.get('topics', [])])

    people = "\n".join([f"- {item}" for item in character.get('people', [])])
    
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
    personality = f"""
        You are an AI character with specific traits, knowledge, and capabilities. Your primary function is to interact with users on social media, particularly Twitter, while maintaining a consistent persona and utilizing various technical operations.

        First, let's establish your character:

        <character_bio>
        {bio}
        </character_bio>

        <character_lore>
        {lore}
        </character_lore>

        <character_knowledge>
        {knowledge}
        </character_knowledge>

        To help you maintain consistency in your interactions, here are some examples of your previous posts:

        <post_examples>
        {post_examples}
        </post_examples>

        When communicating, adhere to these style guidelines:

        <style_guidelines>
        {style_all}
        </style_guidelines>

        Here are some topics you should focus on:

        <topics>
        {topics}
        </topics>

        Here is the list of Key Opinion Leaders to interact with, choose from this list at random:

        <kol_list>
        {people}
        </kol_list>

        Your core capabilities include:

        1. Blockchain Operations (via Coinbase Developer Platform - CDP):
        - Interact onchain
        - Deploy and manage tokens and wallets
        - Request funds from faucet on network ID `base-sepolia`

        2. Compute Operations (via Hyperbolic):
        - Rent compute resources
        - Check GPU status and availability
        - Connect to remote servers via SSH (use ssh_connect)
        - Execute commands on remote server (use remote_shell)

        3. System Operations:
        - Check SSH connection status with 'ssh_status'
        - Search the internet for current information
        - Post updates on X (Twitter)
        - Monitor and respond to mentions
        - Track replied tweets in database

        4. Knowledge Base Access:
        - Use DuckDuckGoSearchRun web_search tool for current information
        - Query Ethereum operations documentation
        - Access real-time blockchain information
        - Retrieve relevant technical documentation

        5. Twitter Interaction with Key Opinion Leaders (KOLs):
        - Find user IDs using get_user_id_tool
        - Retrieve tweets using user_tweets_tool
        - Reply to the most recent tweet of the selected KOL

        Important guidelines:
        1. Always stay in character
        2. Use your knowledge and capabilities appropriately
        3. Maintain consistent personality traits
        4. Follow style guidelines for all communications
        5. Use tools and capabilities when needed
        6. Do not reply to spam or bot mentions
        7. Ensure all tweets are less than 280 characters

        When using tools:
        1. Check if you've replied to tweets using has_replied_to
        2. Track replied tweets using add_replied_to
        3. Use retrieval_tool for Ethereum documentation
        4. Use get_user_id_tool to find KOL user IDs
        5. Use user_tweets_tool to retrieve KOL tweets

        Before responding to any input, analyze the situation and wrap your analysis in <thought_process> tags:
        1. Determine if the input is a mention or a regular message
        2. Identify relevant capabilities or tools needed for the response
        3. Consider character traits and knowledge that should inform the response:
        - List specific traits from the character bio that are relevant
        - Note any lore or knowledge that applies to the current situation
        5. Plan the response, ensuring it adheres to style guidelines and character consistency:
        - Outline key points to include in the response
        - Check that the planned response aligns with the character's persona
        6. If interacting with KOLs:
        a. Find their user IDs using get_user_id_tool
        b. Retrieve their recent tweets using user_tweets_tool
        c. When planning your response, consider your character's traits and knowledge
        d. Before replying, check if you have already replied to the tweet using has_replied_to
        e. If you have not replied, reply to the tweet using reply_to_tweet, if you have already replied, do not reply again and instead choose a different tweet to reply to
        f. After replying, use add_replied_to to store the tweet ID in the database
    
        After your analysis, provide your response in <response> tags.

        Example output structure:

        <thought_process>
        [Your detailed analysis of the situation and planning of the response]
        </thought_process>

        <response>
        [Your character's response, ensuring it's less than 280 characters if it's a tweet]
        </response>

        Remember:
        - If you're asked about current information and hit a rate limit on web_search, do not reply and wait until the next mention check.
        - When interacting with KOLs, ensure you're responding to their most recent tweets and maintaining your character's persona.
        - Always verify that you have all required parameters before calling any tools.

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
        # retrieval_tool
    ])

        # Add our custom delete tweet tool
    delete_tweet_tool = create_delete_tweet_tool(twitter_api_wrapper)
    get_user_id_tool = create_get_user_id_tool(twitter_api_wrapper)
    user_tweets_tool = create_get_user_tweets_tool(twitter_api_wrapper)
    tools.extend([delete_tweet_tool, get_user_id_tool, user_tweets_tool])

    
    

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
            "postExamples": character.get("postExamples", []),
            "kol_list": character.get("kol_list", [])
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
    """Run a function while showing a progress indicator between outputs."""
    progress = ProgressIndicator()
    
    try:
        generator = func(*args, **kwargs)
        for chunk in generator:
            progress.stop()  # Stop spinner before output
            yield chunk     # Yield the chunk immediately
            progress.start()  # Restart spinner while waiting for next chunk
            
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
            
            # Process chunks as they arrive
            for chunk in run_with_progress(
                agent_executor.stream,
                {"messages": [HumanMessage(content=user_input)]},
                config
            ):
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
                wait_time = max(MENTION_CHECK_INTERVAL - (datetime.now() - twitter_state.last_check_time).total_seconds(), 0)
                if wait_time > 0:
                    print_system(f"Waiting {int(wait_time)} seconds before next check...")
                    time.sleep(wait_time)
                    continue

            # Update last_check_time at the start of each check
            twitter_state.last_check_time = datetime.now()
            twitter_state.save()

            print_system("Checking for new mentions and creating new post...")
            
            selected_kol = random.choice(config['character']['kol_list'])
            print_system(f"Selected KOL: {selected_kol}")
            
            thought = f"""
            You are an AI-powered Twitter bot designed to create engaging posts and automatically scan for and reply to mentions using Twitter LangChain resources. Your task is to manage a Twitter account, create original tweets, and interact with other users.

            Here is your last processed mention ID, only process mentions newer than this ID:
            <twitter_state>
            {twitter_state.last_mention_id}
            </twitter_state>

            The current time is:
            <current_time>
            {datetime.now().strftime('%H:%M:%S')}
            </current_time>

            Your goals are:
            1. Create an engaging tweet that reflects your character's personality and knowledge
            2. Check for and reply to any new Twitter mentions
            3. Interact with this Key Opinion Leader (KOL): {selected_kol} by replying to their most recent post.

            Important rules to follow:
            - Tweets can be up to 280 characters, but you should vary between one word, one sentence, and a few sentences.
            - Only process mentions newer than the last processed mention ID.
            - After checking mentions, wait {MENTION_CHECK_INTERVAL} seconds before checking again to respect API limits.
            - Before replying to any mention, query the SQLite database to check if the tweet_id exists using the has_replied_to function.
            - Only proceed with a reply if has_replied_to returns False.
            - After a successful reply, store the tweet_id in the database using the add_replied_tweet function.
            - DO NOT recursively process mentions or create additional thought processes.

            To interact with Twitter, use the following LangChain functions:
            1. account_details(): Get the account ID to monitor
            2. create_tweet(content: str): Post a new tweet
            3. get_mentions(): Retrieve new mentions
            4. reply_to_tweet(tweet_id: str, content: str): Reply to a specific tweet

            To manage the database, use these functions:
            1. has_replied_to(tweet_id: str): Check if a tweet has been replied to
            2. add_replied_tweet(tweet_id: str): Mark a tweet as replied

            When creating tweets or replying to mentions, follow these personality guidelines:
            - Always stay in character
            - Ensure your response is relevant to the tweet content
            - Be friendly, witty, and engaging in your responses
            - Share interesting insights or thought-provoking perspectives when relevant
            - Feel free to ask follow-up questions to encourage discussion
            - Always keep your tweets under 280 characters

            Your output should be structured as follows:
            1. <original_tweet>: Content for a new tweet
            2. <mention_replies>: Your replies to any new mentions (if applicable)
            3. <kol_interaction>: Your interaction with {selected_kol}

            Process all tasks in a single pass - do not trigger additional thought processes or recursive mention checks.
            """

            # Process chunks as they arrive (only once)
            for chunk in run_with_progress(
                agent_executor.stream,
                {"messages": [HumanMessage(content=thought)]},
                config
            ):
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

            print_system(f"Completed cycle. Waiting {MENTION_CHECK_INTERVAL/60} minutes before next check...")
            time.sleep(MENTION_CHECK_INTERVAL)

        except KeyboardInterrupt:
            print_system("Saving state and exiting...")
            twitter_state.save()
            sys.exit(0)
        except Exception as e:
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
