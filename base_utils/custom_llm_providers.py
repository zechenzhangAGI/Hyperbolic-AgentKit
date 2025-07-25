"""
Custom LLM providers for special API endpoints.
Includes Harvard's custom OpenAI endpoint and other custom implementations.
"""

import os
import json
import requests
from typing import Any, List, Optional, Dict, Iterator
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import SimpleChatModel, BaseChatModel
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field, BaseModel


class HarvardChatModel(SimpleChatModel):
    """Custom chat model for Harvard's OpenAI endpoint."""
    
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4.1-mini-2025-04-14")
    temperature: float = Field(default=1.0)
    base_url: str = Field(default="https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1")
    
    def __init__(self, **kwargs):
        """Initialize Harvard chat model."""
        api_key = kwargs.get("api_key") or os.getenv("HARVARD_API_KEY")
        if not api_key:
            raise ValueError("Harvard API key required. Set HARVARD_API_KEY env var or pass api_key parameter.")
        
        kwargs["api_key"] = api_key
        super().__init__(**kwargs)
    
    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call Harvard's API endpoint."""
        # Convert messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
        
        # Prepare request
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key  # Harvard uses 'api-key' header
        }
        
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature
        }
        
        if stop:
            payload["stop"] = stop
        
        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Harvard API call failed after {max_retries} attempts: {str(e)}")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url
        }
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "harvard-openai"


class CustomOpenAIChatModel(SimpleChatModel):
    """Generic custom OpenAI-compatible chat model."""
    
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7)
    base_url: str = Field(default="")
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    
    def __init__(self, **kwargs):
        """Initialize custom OpenAI chat model."""
        api_key = kwargs.get("api_key") or os.getenv("CUSTOM_OPENAI_API_KEY")
        base_url = kwargs.get("base_url") or os.getenv("CUSTOM_OPENAI_BASE_URL")
        
        if not api_key:
            raise ValueError("API key required. Set CUSTOM_OPENAI_API_KEY env var or pass api_key parameter.")
        if not base_url:
            raise ValueError("Base URL required. Set CUSTOM_OPENAI_BASE_URL env var or pass base_url parameter.")
        
        kwargs["api_key"] = api_key
        kwargs["base_url"] = base_url
        
        # Parse custom headers from environment if not provided
        if not kwargs.get("custom_headers"):
            headers_str = os.getenv("CUSTOM_OPENAI_HEADERS", "{}")
            try:
                kwargs["custom_headers"] = json.loads(headers_str)
            except:
                kwargs["custom_headers"] = {}
        
        super().__init__(**kwargs)
    
    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call custom OpenAI-compatible API endpoint."""
        # Convert messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
        
        # Prepare request
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        headers.update(self.custom_headers)
        
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature
        }
        
        if stop:
            payload["stop"] = stop
        
        # Make request
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise RuntimeError(f"Custom OpenAI API call failed: {str(e)}")
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url
        }
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "custom-openai"