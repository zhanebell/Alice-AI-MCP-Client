"""
Enhanced AI Agent System Configuration
Supports multiple LLM providers and configurable model settings
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class ModelConfig(BaseModel):
    """Configuration for a specific model"""
    model_config = {"protected_namespaces": ()}
    
    provider: LLMProvider
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key_env: Optional[str] = None  # Environment variable name for API key
    base_url: Optional[str] = None  # For custom endpoints like Ollama

class AIConfig:
    """Centralized AI configuration"""
    
    # Available model configurations
    MODELS = {
        # Groq models
        "llama-70b": ModelConfig(
            provider=LLMProvider.GROQ,
            model_name="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048,
            api_key_env="GROQ_API_KEY"
        ),
        "llama-8b": ModelConfig(
            provider=LLMProvider.GROQ,
            model_name="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=2048,
            api_key_env="GROQ_API_KEY"
        ),
        "mixtral": ModelConfig(
            provider=LLMProvider.GROQ,
            model_name="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=2048,
            api_key_env="GROQ_API_KEY"
        ),
        
        # OpenAI models
        "gpt-4": ModelConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=2048,
            api_key_env="OPENAI_API_KEY"
        ),
        "gpt-3.5-turbo": ModelConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2048,
            api_key_env="OPENAI_API_KEY"
        ),
        
        # Anthropic models
        "claude-3.5-sonnet": ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2048,
            api_key_env="ANTHROPIC_API_KEY"
        ),
        
        # Ollama (local) models
        "llama3-local": ModelConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llama3",
            temperature=0.7,
            max_tokens=2048,
            base_url="http://localhost:11434"
        )
    }
    
    @classmethod
    def get_default_model(cls) -> str:
        """Get the default model to use"""
        # Check environment variable for preferred model
        default = os.getenv("ALICE_DEFAULT_MODEL", "llama-70b")
        if default in cls.MODELS:
            return default
        return "llama-70b"
    
    @classmethod
    def get_model_config(cls, model_key: str) -> ModelConfig:
        """Get configuration for a specific model"""
        if model_key not in cls.MODELS:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(cls.MODELS.keys())}")
        return cls.MODELS[model_key]
    
    @classmethod
    def list_available_models(cls) -> Dict[str, str]:
        """List all available models with their descriptions"""
        return {
            key: f"{config.provider.value} - {config.model_name}"
            for key, config in cls.MODELS.items()
        }
    
    @classmethod
    def is_model_available(cls, model_key: str) -> bool:
        """Check if a model is available (API key configured)"""
        if model_key not in cls.MODELS:
            return False
        
        config = cls.MODELS[model_key]
        
        # For Ollama, we assume it's available if specified
        if config.provider == LLMProvider.OLLAMA:
            return True
        
        # For cloud providers, check if API key is set
        if config.api_key_env:
            api_key = os.getenv(config.api_key_env)
            return api_key is not None and api_key.strip() != ""
        
        return False
