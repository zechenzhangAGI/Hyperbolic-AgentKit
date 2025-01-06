from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from custom_twitter_actions import get_user_tweets, get_user_id
from utils import print_system, print_error
import asyncio
import os
import random

# Add Tweet model definition that was missing
class Tweet(BaseModel):
    id: str
    text: str
    created_at: str
    author_id: str

class TweetKnowledgeBase:
    def __init__(self, collection_name: str = "twitter_knowledge"):
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use a more advanced embedding model
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        
        # Create embedding function that matches ChromaDB's expected interface
        class EmbeddingFunction:
            def __init__(self, model):
                self.model = model
            
            def __call__(self, input: List[str]) -> List[List[float]]:
                embeddings = self.model.encode(input)
                return embeddings.tolist()
        
        embedding_func = EmbeddingFunction(self.embedding_model)
        
        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_func
            )
        except Exception as e:
            print(f"Error initializing collection: {e}")
            raise

    def add_tweets(self, tweets: List[Tweet]):
        """Add tweets to the knowledge base."""
        documents = [tweet.text for tweet in tweets]
        ids = [tweet.id for tweet in tweets]
        metadata = [
            {
                "author_id": tweet.author_id,
                "created_at": tweet.created_at,
            }
            for tweet in tweets
        ]
        
        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadata
        )

    def query_knowledge_base(self, query: str, n_results: int = 10) -> List[Dict]:
        """Query the knowledge base for relevant tweets."""
        try:
            # Add logging for debugging
            print_system(f"Querying knowledge base with: {query}")
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'][0]:
                print_system("No results found in knowledge base")
                return []
                
            formatted_results = []
            for doc, metadata, distance in zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            ):
                # Format timestamp for readability
                created_at = datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
                formatted_date = created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                
                formatted_results.append({
                    "text": doc,
                    "metadata": {
                        **metadata,
                        "created_at": formatted_date
                    },
                    "relevance_score": 1 - distance  # Convert distance to similarity score
                })
            
            # Sort by relevance score
            formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            print_system(f"Found {len(formatted_results)} relevant tweets")
            return formatted_results
            
        except Exception as e:
            print_error(f"Error querying knowledge base: {e}")
            return []

    def format_query_results(self, results: List[Dict]) -> str:
        """Format query results into a readable string."""
        if not results:
            return "No relevant tweets found in knowledge base."
            
        formatted_output = []
        for result in results:
            formatted_output.append(
                f"Tweet from {result['metadata']['created_at']}\n"
                f"Relevance: {result['relevance_score']:.2f}\n"
                f"Content: {result['text']}\n"
            )
            
        return "\n---\n".join(formatted_output)

    def get_collection_stats(self) -> Dict:
        """Get statistics about the knowledge base collection."""
        try:
            count = self.collection.count()
            metadata = self.collection.get()
            last_update = None
            if metadata.get("metadatas"):
                # Get most recent tweet timestamp
                last_update = max(m["created_at"] for m in metadata["metadatas"])
                last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            
            print_system(f"Knowledge base contains {count} tweets")
            return {
                "count": count,
                "last_update": last_update or datetime.now()
            }
        except Exception as e:
            print_error(f"Error getting collection stats: {str(e)}")
            return {"count": 0, "last_update": datetime.now()}

    def clear_collection(self) -> bool:
        """Clear all tweets from the knowledge base."""
        try:
            print_system("Clearing knowledge base collection...")
            ids = self.collection.get()["ids"]
            if ids:  # Only attempt to delete if there are IDs
                self.collection.delete(ids=ids)
                print_system("Knowledge base cleared successfully")
            else:
                print_system("Knowledge base is already empty")
            return True
        except Exception as e:
            print_error(f"Error clearing knowledge base: {str(e)}")
            return False

async def update_knowledge_base(twitter_api_wrapper, knowledge_base, kol_list: List[Dict]):
    """Update the knowledge base with recent tweets from top KOLs."""
    TOP_KOLS = 5
    TWEETS_PER_KOL = 15
    REQUEST_DELAY = 5
    
    update_time = datetime.now()
    all_tweets = []
    top_kols = random.sample(kol_list, min(TOP_KOLS, len(kol_list)))
    
    print_system(f"Starting knowledge base update at {update_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Clear existing knowledge base
    try:
        knowledge_base.clear_collection()
        print_system("Cleared existing knowledge base")
    except Exception as e:
        print_error(f"Error clearing knowledge base: {e}")
        return
    
    print_system(f"Processing {len(top_kols)} randomly selected KOLs...")
    
    for kol in top_kols:
        print_system(f"Fetching {TWEETS_PER_KOL} tweets for {kol['username']}")
        kol_tweets = []
        
        response = twitter_api_wrapper.run_action(
            get_user_tweets, 
            user_id=kol['user_id'],
            max_results=TWEETS_PER_KOL
        )
        
        # Check for rate limit error immediately
        if isinstance(response, str) and "429 Too Many Requests" in response:
            print_error("X API rate limit reached. Please try again in 15 minutes.")
            return  # Exit the function immediately
            
        # Rest of the tweet processing logic...
        if isinstance(response, str):
            tweet_blocks = [block.strip() for block in response.split("\n\n") if block.strip()]
            
            for block in tweet_blocks:
                if "[Tweet ID:" in block:
                    try:
                        # Extract tweet ID
                        tweet_parts = block.split("]")
                        tweet_id = tweet_parts[0].split("[Tweet ID: ")[1].strip()
                        
                        # Set created_at to current time if not found
                        created_at = datetime.now().isoformat()
                        try:
                            created_at = next(part.split("[Created: ")[1].strip() 
                                           for part in tweet_parts if "[Created: " in part)
                        except StopIteration:
                            # If no timestamp found, keep using current time
                            pass
                        
                        # Get tweet text by removing the Tweet ID metadata
                        tweet_text = block.replace(f"[Tweet ID: {tweet_id}]", "").strip()
                        
                        if tweet_id and tweet_text:
                            print_system(f"Successfully parsed tweet ID: {tweet_id}")
                            kol_tweets.append(
                                Tweet(
                                    id=tweet_id,
                                    text=tweet_text,
                                    created_at=created_at,
                                    author_id=kol['user_id']
                                )
                            )
                    except Exception as e:
                        print_error(f"Error parsing tweet block: {str(e)}")
                        print_error(f"Problematic block: {block}")
                        continue
            
            print_system(f"Processed {len(kol_tweets)} tweets from {kol['username']}")
            all_tweets.extend(kol_tweets)  # Add KOL's tweets to total
            
    if all_tweets:
        print_system(f"Adding {len(all_tweets)} tweets to knowledge base")
        try:
            knowledge_base.add_tweets(all_tweets)
            print_system(f"Knowledge base updated successfully at {update_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except Exception as e:
            print_error(f"Error updating knowledge base: {e}")
    else:
        print_system("No new tweets to add to knowledge base") 