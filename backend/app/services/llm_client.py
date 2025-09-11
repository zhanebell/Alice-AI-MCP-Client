"""
Unified LLM Client for handling multiple AI providers
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from .ai_config import AIConfig, LLMProvider, ModelConfig

@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass 
class ChatResponse:
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None

class LLMClient:
    """Unified client for multiple LLM providers"""
    
    def __init__(self, model_key: Optional[str] = None):
        self.model_key = model_key or AIConfig.get_default_model()
        self.config = AIConfig.get_model_config(self.model_key)
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider"""
        try:
            if self.config.provider == LLMProvider.GROQ:
                import groq
                api_key = os.getenv(self.config.api_key_env)
                if not api_key:
                    raise ValueError(f"Missing API key: {self.config.api_key_env}")
                self._client = groq.Groq(api_key=api_key)
                
            elif self.config.provider == LLMProvider.OPENAI:
                import openai
                api_key = os.getenv(self.config.api_key_env)
                if not api_key:
                    raise ValueError(f"Missing API key: {self.config.api_key_env}")
                self._client = openai.OpenAI(api_key=api_key)
                
            elif self.config.provider == LLMProvider.ANTHROPIC:
                import anthropic
                api_key = os.getenv(self.config.api_key_env)
                if not api_key:
                    raise ValueError(f"Missing API key: {self.config.api_key_env}")
                self._client = anthropic.Anthropic(api_key=api_key)
                
            elif self.config.provider == LLMProvider.OLLAMA:
                import requests
                # For Ollama, we'll use direct HTTP requests
                base_url = self.config.base_url or "http://localhost:11434"
                # Test connection
                response = requests.get(f"{base_url}/api/tags", timeout=5)
                if response.status_code != 200:
                    raise ConnectionError("Cannot connect to Ollama server")
                self._client = base_url
                
        except ImportError as e:
            raise ImportError(f"Missing required package for {self.config.provider}: {e}")
        except Exception as e:
            print(f"Warning: Failed to initialize {self.config.provider} client: {e}")
            self._client = None
    
    def is_available(self) -> bool:
        """Check if the client is properly initialized"""
        return self._client is not None
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Send chat completion request"""
        if not self.is_available():
            raise RuntimeError(f"LLM client not available for {self.config.provider}")
        
        # Override config with any provided kwargs
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        if self.config.provider == LLMProvider.GROQ:
            return self._groq_chat(messages, temperature, max_tokens)
        elif self.config.provider == LLMProvider.OPENAI:
            return self._openai_chat(messages, temperature, max_tokens)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return self._anthropic_chat(messages, temperature, max_tokens)
        elif self.config.provider == LLMProvider.OLLAMA:
            return self._ollama_chat(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _groq_chat(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> ChatResponse:
        """Handle Groq chat completion"""
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return ChatResponse(
            content=response.choices[0].message.content or "",
            model=self.config.model_name,
            provider="groq",
            usage={
                "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(response.usage, 'total_tokens', 0)
            }
        )
    
    def _openai_chat(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> ChatResponse:
        """Handle OpenAI chat completion"""
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return ChatResponse(
            content=response.choices[0].message.content or "",
            model=self.config.model_name,
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    
    def _anthropic_chat(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> ChatResponse:
        """Handle Anthropic Claude chat completion"""
        # Claude API has a different format - system message separate
        system_message = None
        formatted_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        
        kwargs = {
            "model": self.config.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        response = self._client.messages.create(**kwargs)
        
        return ChatResponse(
            content=response.content[0].text if response.content else "",
            model=self.config.model_name,
            provider="anthropic",
            usage={
                "prompt_tokens": getattr(response.usage, 'input_tokens', 0),
                "completion_tokens": getattr(response.usage, 'output_tokens', 0),
                "total_tokens": getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0)
            }
        )
    
    def _ollama_chat(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> ChatResponse:
        """Handle Ollama chat completion"""
        import requests
        
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        payload = {
            "model": self.config.model_name,
            "messages": formatted_messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(
            f"{self._client}/api/chat",
            json=payload,
            timeout=120  # Ollama can be slow
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Ollama error: {response.text}")
        
        result = response.json()
        
        return ChatResponse(
            content=result.get("message", {}).get("content", ""),
            model=self.config.model_name,
            provider="ollama",
            usage={
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            }
        )

# Convenience function
def create_llm_client(model_key: Optional[str] = None) -> LLMClient:
    """Create an LLM client with the specified model"""
    return LLMClient(model_key)

# Test function
def test_available_models() -> Dict[str, bool]:
    """Test which models are currently available"""
    results = {}
    for model_key in AIConfig.MODELS.keys():
        try:
            client = LLMClient(model_key)
            results[model_key] = client.is_available()
        except Exception as e:
            results[model_key] = False
            print(f"Model {model_key} not available: {e}")
    return results
