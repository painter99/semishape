"""Unified LLM client for multiple providers.

Supports OpenRouter API and local Ollama with unified interface.
Handles configuration from environment variables, rate limiting,
and error handling with retries.
"""

# CRITICAL: Load environment variables FIRST before anything else
# Direct file reading without dotenv dependency
import os
from pathlib import Path

def _load_env_file(env_path: str):
    """Load environment variables from file directly."""
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Only set if not already set
                    if key and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass

# Load from Agent Zero .env (contains API keys)
_load_env_file('/a0/usr/.env')

# Now import the rest
import time
import json
import logging
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import requests
logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # "system", "user", "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """LLM response structure."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    
    @property
    def token_count(self) -> int:
        return self.usage.get("total_tokens", 0)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: str = "openrouter"
    model: str = "ibm/granite-4-h-micro"
    api_key: str = field(default_factory=lambda: os.environ.get("API_KEY_OPENROUTER", ""))
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    
    def __post_init__(self):
        # Ensure API key is set from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("API_KEY_OPENROUTER", "")
        # Set base URL based on provider
        if self.provider == "ollama":
            self.base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        provider = os.environ.get("LLM_PROVIDER", "openrouter")
        model = os.environ.get("LLM_MODEL", "ibm/granite-4-h-micro")
        return cls(provider=provider, model=model)


class BaseLLMClient(ABC):
    """Base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text as stream."""
        pass
    
    def complete(self, messages=None, prompt=None, **kwargs) -> LLMResponse:
        """Complete method for compatibility with inference.py.
        
        Accepts either:
        - messages=[ChatMessage(...), ...] (list of ChatMessage objects)
        - messages=[{"role": "user", "content": "..."}] (list of dicts)
        - prompt="..." (fallback)
        """
        if messages is None and prompt is None:
            raise ValueError("Either messages or prompt must be provided")
        
        # Convert ChatMessage objects to dicts if needed
        formatted_messages = []
        for msg in (messages or []):
            if hasattr(msg, 'to_dict'):
                formatted_messages.append(msg.to_dict())
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        
        # Use messages if available, otherwise use prompt
        result = self.generate(prompt or "", messages=formatted_messages, **kwargs)
        return LLMResponse(
            content=result,
            model=self.config.model,
            usage={},
            finish_reason="stop"
        )
    
    def stream_complete(self, messages=None, prompt=None, **kwargs) -> Generator[str, None, None]:
        """Stream complete method for compatibility."""
        if messages is None and prompt is None:
            raise ValueError("Either messages or prompt must be provided")
        
        formatted_messages = []
        for msg in (messages or []):
            if hasattr(msg, 'to_dict'):
                formatted_messages.append(msg.to_dict())
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
        
        return self.generate_stream(prompt or "", messages=formatted_messages, **kwargs)


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Verify API key after env is loaded
        self.api_key = config.api_key or os.environ.get("API_KEY_OPENROUTER", "")
        if not self.api_key:
            raise ValueError("API_KEY_OPENROUTER is required for OpenRouter")
        self.base_url = config.base_url
        self.model = config.model
        self._client = None
    
    @property
    def client(self):
        """Lazy load OpenRouter client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text as stream."""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenRouter stream error: {e}")
            raise


class OllamaClient(BaseLLMClient):
    """Local Ollama client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url
        self.model = config.model
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        import requests
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                }
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text as stream."""
        import requests
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                }
            },
            stream=True,
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "response" in data:
                    yield data["response"]


def create_client(config: LLMConfig) -> BaseLLMClient:
    """Create LLM client based on configuration."""
    if config.provider == "openrouter":
        return OpenRouterClient(config)
    elif config.provider == "ollama":
        return OllamaClient(config)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
