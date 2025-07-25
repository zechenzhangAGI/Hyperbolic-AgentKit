"""
Enhanced custom LLM providers with tool calling support.
"""

import os
import json
import requests
from typing import Any, List, Optional, Dict, Iterator, Sequence, Union, Type
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.pydantic_v1 import Field, root_validator
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool, convert_to_openai_function
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.runnables import Runnable


class HarvardChatModel(BaseChatModel):
    """Harvard OpenAI-compatible chat model with tool calling support."""
    
    api_key: str = ""
    model: str = "gpt-4.1-mini-2025-04-14"
    temperature: float = 1.0
    base_url: str = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1"
    _tools: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        allow_population_by_field_name = True
    
    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that API key exists."""
        api_key = values.get("api_key") or os.getenv("HARVARD_API_KEY")
        if not api_key:
            raise ValueError("Harvard API key required. Set HARVARD_API_KEY env var or pass api_key parameter.")
        values["api_key"] = api_key
        return values
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "harvard-openai"
    
    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Convert LangChain messages to OpenAI format."""
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                message_dict = {"role": "assistant", "content": msg.content}
                
                # Add tool calls if present
                if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                    message_dict['tool_calls'] = msg.additional_kwargs['tool_calls']
                elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Convert tool calls to OpenAI format
                    message_dict['tool_calls'] = [
                        {
                            "id": tc.get("id", f"call_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"]) if isinstance(tc["args"], dict) else tc["args"]
                            }
                        }
                        for i, tc in enumerate(msg.tool_calls)
                    ]
                
                openai_messages.append(message_dict)
            elif isinstance(msg, ToolMessage):
                openai_messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id
                })
                
        return openai_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from Harvard API."""
        # Convert messages
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare request
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        
        payload = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature
        }
        
        # Add tools if they were bound
        if hasattr(self, '_tools') and self._tools:
            payload["tools"] = self._tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        if stop:
            payload["stop"] = stop
        
        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                choice = result["choices"][0]
                message = choice["message"]
                
                # Create AIMessage with proper tool calls if present
                ai_message = AIMessage(content=message.get("content", ""))
                
                # Handle tool calls
                if "tool_calls" in message:
                    tool_calls = []
                    for tc in message["tool_calls"]:
                        tool_calls.append({
                            "name": tc["function"]["name"],
                            "args": json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"],
                            "id": tc["id"]
                        })
                    ai_message.tool_calls = tool_calls
                    ai_message.additional_kwargs["tool_calls"] = message["tool_calls"]
                
                generation = ChatGeneration(message=ai_message)
                return ChatResult(generations=[generation])
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Harvard API call failed after {max_retries} attempts: {str(e)}")
                import time
                time.sleep(2 ** attempt)
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generation - just calls sync version for now."""
        return self._generate(messages, stop, run_manager, **kwargs)
    
    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type, BaseTool]],
        **kwargs: Any
    ) -> "HarvardChatModel":
        """Bind tools to the model."""
        formatted_tools = []
        for tool in tools:
            if isinstance(tool, dict):
                formatted_tools.append(tool)
            elif isinstance(tool, type) and issubclass(tool, BaseTool):
                formatted_tools.append(convert_to_openai_tool(tool))
            elif isinstance(tool, BaseTool):
                formatted_tools.append(convert_to_openai_tool(tool))
            else:
                formatted_tools.append(convert_to_openai_function(tool))
        
        # Create a new instance with tools bound
        new_model = self.__class__(**self.dict())
        new_model._tools = formatted_tools
        return new_model
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url
        }