"""
Harvard-specific OpenAI wrapper that properly handles authentication.
"""

import os
import httpx
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI


class HarvardChatOpenAI(ChatOpenAI):
    """
    OpenAI chat model that uses Harvard's custom authentication.
    Overrides the HTTP client to use 'api-key' header instead of Authorization.
    """
    
    def __init__(self, **kwargs):
        # Get Harvard API key
        harvard_api_key = kwargs.pop("harvard_api_key", None) or os.getenv("HARVARD_API_KEY")
        if not harvard_api_key:
            raise ValueError("Harvard API key required")
        
        # Set base URL if not provided
        if "openai_api_base" not in kwargs and "base_url" not in kwargs:
            kwargs["openai_api_base"] = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1"
        
        # Use a dummy OpenAI key since we'll override the auth header
        kwargs["openai_api_key"] = "dummy-key"
        
        # Store Harvard key for later use
        self._harvard_api_key = harvard_api_key
        
        # Default temperature for Harvard
        if "temperature" not in kwargs:
            kwargs["temperature"] = 1.0
        
        super().__init__(**kwargs)
    
    @property
    def _client_params(self) -> Dict[str, Any]:
        """Override to use custom HTTP client with Harvard auth."""
        params = super()._client_params
        
        # Create custom httpx client with Harvard auth
        http_client = httpx.Client(
            headers={
                "api-key": self._harvard_api_key,
                # Remove the Authorization header that would be added
            },
            # Copy other settings from default client
            timeout=params.get("timeout", httpx.Timeout(timeout=600.0)),
        )
        
        params["http_client"] = http_client
        
        # Remove the api_key from params to prevent Authorization header
        if "api_key" in params:
            del params["api_key"]
        
        return params
    
    @property
    def _async_client_params(self) -> Dict[str, Any]:
        """Override for async client as well."""
        params = super()._async_client_params
        
        # Create custom async httpx client
        http_client = httpx.AsyncClient(
            headers={
                "api-key": self._harvard_api_key,
            },
            timeout=params.get("timeout", httpx.Timeout(timeout=600.0)),
        )
        
        params["http_client"] = http_client
        
        # Remove the api_key from params
        if "api_key" in params:
            del params["api_key"]
        
        return params