"""
LLM Factory for creating language models from different providers.
Supports Anthropic, OpenAI, Google, and other providers.
"""

import os
import json
from typing import Dict, Any, Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from base_utils.custom_llm_providers import CustomOpenAIChatModel
from base_utils.harvard_openai_wrapper import HarvardChatOpenAI
from dotenv import load_dotenv

# Optional imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

load_dotenv()


class LLMConfig:
    """Configuration for LLM models."""
    
    # Provider constants
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"
    HARVARD = "harvard"  # Harvard's custom OpenAI endpoint
    CUSTOM_OPENAI = "custom_openai"  # Generic custom OpenAI-compatible endpoint
    
    # Default models for each provider
    DEFAULT_MODELS = {
        ANTHROPIC: "claude-sonnet-4-20250514",
        OPENAI: "gpt-4-turbo-preview",
        GOOGLE: "gemini-pro",
        OLLAMA: "llama2",
        HARVARD: "gpt-4.1-mini-2025-04-14",
        CUSTOM_OPENAI: "gpt-4"
    }
    
    # Model aliases for easier access
    MODEL_ALIASES = {
        # Anthropic models
        "claude-opus": "claude-3-opus-20240229",
        "claude-sonnet": "claude-3-sonnet-20240229",
        "claude-haiku": "claude-3-haiku-20240307",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        
        # OpenAI models
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-3.5": "gpt-3.5-turbo",
        "o1": "o1-preview",
        "o1-mini": "o1-mini",
        "o3": "o3",  # When available
        "o3-mini": "o3-mini",  # When available
        
        # Google models
        "gemini": "gemini-pro",
        "gemini-vision": "gemini-pro-vision",
        
        # Local models (Ollama)
        "llama2": "llama2",
        "mistral": "mistral",
        "codellama": "codellama",
        
        # Harvard models
        "harvard-o3-mini": "o3-mini-2025-01-31",
        "harvard-gpt4-mini": "gpt-4.1-mini-2025-04-14"
    }


class LLMFactory:
    """Factory class for creating LLM instances from different providers."""
    
    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseChatModel:
        """
        Create an LLM instance based on provider and model.
        
        Args:
            provider: The LLM provider (anthropic, openai, google, ollama)
            model: The specific model to use
            **kwargs: Additional arguments to pass to the LLM constructor
            
        Returns:
            BaseChatModel: The initialized LLM instance
        """
        # Get provider and model from environment if not specified
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", LLMConfig.ANTHROPIC).lower()
        
        if model is None:
            model = os.getenv("LLM_MODEL", LLMConfig.DEFAULT_MODELS.get(provider))
        
        # Resolve model aliases
        model = LLMConfig.MODEL_ALIASES.get(model, model)
        
        # Create LLM based on provider
        if provider == LLMConfig.ANTHROPIC:
            return LLMFactory._create_anthropic(model, **kwargs)
        elif provider == LLMConfig.OPENAI:
            return LLMFactory._create_openai(model, **kwargs)
        elif provider == LLMConfig.GOOGLE:
            return LLMFactory._create_google(model, **kwargs)
        elif provider == LLMConfig.OLLAMA:
            return LLMFactory._create_ollama(model, **kwargs)
        elif provider == LLMConfig.HARVARD:
            return LLMFactory._create_harvard(model, **kwargs)
        elif provider == LLMConfig.CUSTOM_OPENAI:
            return LLMFactory._create_custom_openai(model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @staticmethod
    def _create_anthropic(model: str, **kwargs) -> ChatAnthropic:
        """Create Anthropic Claude model."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        default_kwargs = {
            "model": model,
            "anthropic_api_key": api_key,
            "max_tokens": 4096,
            "temperature": 0.7
        }
        default_kwargs.update(kwargs)
        
        return ChatAnthropic(**default_kwargs)
    
    @staticmethod
    def _create_openai(model: str, **kwargs) -> ChatOpenAI:
        """Create OpenAI model (including o3 when available)."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Special handling for o1/o3 models (they have different parameters)
        if model.startswith(("o1", "o3")):
            default_kwargs = {
                "model": model,
                "openai_api_key": api_key,
                "temperature": 1,  # o1/o3 models use fixed temperature
            }
            # Remove unsupported parameters for o1/o3
            kwargs.pop("max_tokens", None)
            kwargs.pop("top_p", None)
        else:
            default_kwargs = {
                "model": model,
                "openai_api_key": api_key,
                "temperature": 0.7,
                "max_tokens": 4096
            }
        
        default_kwargs.update(kwargs)
        
        return ChatOpenAI(**default_kwargs)
    
    @staticmethod
    def _create_google(model: str, **kwargs):
        """Create Google Gemini model."""
        if not HAS_GOOGLE:
            raise ImportError("Google Gemini support requires 'langchain-google-genai'. Install with: pip install langchain-google-genai")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        default_kwargs = {
            "model": model,
            "google_api_key": api_key,
            "temperature": 0.7,
            "max_output_tokens": 4096
        }
        default_kwargs.update(kwargs)
        
        return ChatGoogleGenerativeAI(**default_kwargs)
    
    @staticmethod
    def _create_ollama(model: str, **kwargs) -> ChatOllama:
        """Create local Ollama model."""
        default_kwargs = {
            "model": model,
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "temperature": 0.7
        }
        default_kwargs.update(kwargs)
        
        return ChatOllama(**default_kwargs)
    
    @staticmethod
    def _create_harvard(model: str, **kwargs) -> ChatOpenAI:
        """Create Harvard OpenAI model with custom endpoint."""
        api_key = os.getenv("HARVARD_API_KEY")
        if not api_key:
            raise ValueError("HARVARD_API_KEY not found in environment")
        
        # Harvard requires both Authorization and api-key headers
        default_kwargs = {
            "model": model,
            "openai_api_key": api_key,  # This sets Authorization: Bearer <key>
            "openai_api_base": "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1",
            "temperature": 1,  # Harvard models typically use temperature=1
            "default_headers": {
                "api-key": api_key  # Harvard also needs this header
            }
        }
        
        default_kwargs.update(kwargs)
        
        return ChatOpenAI(**default_kwargs)
    
    @staticmethod
    def _create_custom_openai(model: str, **kwargs) -> CustomOpenAIChatModel:
        """Create custom OpenAI-compatible model with configurable endpoint."""
        api_key = os.getenv("CUSTOM_OPENAI_API_KEY")
        base_url = os.getenv("CUSTOM_OPENAI_BASE_URL")
        
        if not api_key:
            raise ValueError("CUSTOM_OPENAI_API_KEY not found in environment")
        if not base_url:
            raise ValueError("CUSTOM_OPENAI_BASE_URL not found in environment")
        
        default_kwargs = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "temperature": 0.7
        }
        
        # Check if custom headers are needed
        custom_headers = os.getenv("CUSTOM_OPENAI_HEADERS")
        if custom_headers:
            try:
                headers = json.loads(custom_headers)
                default_kwargs["custom_headers"] = headers
            except:
                pass
        
        default_kwargs.update(kwargs)
        
        return CustomOpenAIChatModel(**default_kwargs)
    
    @staticmethod
    def get_available_models(provider: Optional[str] = None) -> Dict[str, list]:
        """Get available models for each provider or a specific provider."""
        all_models = {
            LLMConfig.ANTHROPIC: [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229", 
                "claude-3-haiku-20240307",
                "claude-sonnet-4-20250514"
            ],
            LLMConfig.OPENAI: [
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini",
                "o3",  # When available
                "o3-mini"  # When available
            ],
            LLMConfig.GOOGLE: [
                "gemini-pro",
                "gemini-pro-vision"
            ],
            LLMConfig.OLLAMA: [
                "llama2",
                "mistral",
                "codellama",
                "mixtral"
            ],
            LLMConfig.HARVARD: [
                "o3-mini-2025-01-31",
                "gpt-4.1-mini-2025-04-14"
            ],
            LLMConfig.CUSTOM_OPENAI: [
                # Models depend on the custom endpoint
                "gpt-4", "gpt-3.5-turbo", "custom"
            ]
        }
        
        if provider:
            return {provider: all_models.get(provider, [])}
        return all_models
    
    @staticmethod
    def validate_model(provider: str, model: str) -> bool:
        """Check if a model is available for a given provider."""
        # Resolve aliases first
        model = LLMConfig.MODEL_ALIASES.get(model, model)
        
        available_models = LLMFactory.get_available_models(provider)
        provider_models = available_models.get(provider, [])
        
        return model in provider_models