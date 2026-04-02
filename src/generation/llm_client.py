"""Unified LLM client for multiple providers.

Supports OpenRouter API and local Ollama with unified interface.
Handles configuration from environment variables, rate limiting,
and error handling with retries.
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: str = "openrouter"  # openrouter or ollama
    model: str = "openai/gpt-4o-mini"  # default model
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Provider-specific defaults
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_base_url: str = "http://localhost:11434"
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Load configuration from environment variables.
        
        Environment variables:
        - API_KEY_OPENROUTER: OpenRouter API key
        - API_KEY_OLLAMA: Ollama API key (optional)
        - LLM_PROVIDER: 'openrouter' or 'ollama'
        - LLM_MODEL: Model identifier
        - LLM_BASE_URL: Override base URL
        - LLM_MAX_TOKENS: Max tokens for response
        - LLM_TEMPERATURE: Sampling temperature
        """
        provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
        
        # Determine API key based on provider
        if provider == "ollama":
            api_key = os.getenv("API_KEY_OLLAMA", "")
            base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
            model = os.getenv("LLM_MODEL", "llama3.2")
        else:  # openrouter
            api_key = os.getenv("API_KEY_OPENROUTER", "")
            base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
            model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
        
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            top_p=float(os.getenv("LLM_TOP_P", "0.9")),
            timeout=int(os.getenv("LLM_TIMEOUT", "120")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("LLM_RETRY_DELAY", "1.0")),
        )


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # system, user, assistant
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from LLM completion."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    raw_response: Dict[str, Any] = field(default_factory=dict)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def complete(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """Complete a chat conversation."""
        pass
    
    @abstractmethod
    def stream_complete(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream completion chunks."""
        pass


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("API_KEY_OPENROUTER is required for OpenRouter")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/semishape",
            "X-Title": "SemiShape CAD Assistant"
        })
    
    def _make_request(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request payload."""
        return {
            "model": kwargs.get("model", self.config.model),
            "messages": [m.to_dict() for m in messages],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "stream": stream,
        }
    
    def _retry_request(
        self,
        url: str,
        payload: Dict[str, Any],
        stream: bool = False
    ) -> requests.Response:
        """Make request with retry logic."""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=self.config.timeout,
                    stream=stream
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", self.config.retry_delay * 2))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                
        raise RuntimeError(f"Request failed after {self.config.max_retries} retries: {last_error}")
    
    def complete(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """Complete a chat conversation."""
        url = f"{self.config.base_url}/chat/completions"
        payload = self._make_request(messages, stream=False, **kwargs)
        
        response = self._retry_request(url, payload)
        data = response.json()
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", self.config.model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data
        )
    
    def stream_complete(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream completion chunks."""
        url = f"{self.config.base_url}/chat/completions"
        payload = self._make_request(messages, stream=True, **kwargs)
        
        response = self._retry_request(url, payload, stream=True)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue


class OllamaClient(BaseLLMClient):
    """Ollama local API client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.session = requests.Session()
    
    def _make_request(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request payload for Ollama API."""
        return {
            "model": kwargs.get("model", self.config.model),
            "messages": [m.to_dict() for m in messages],
            "options": {
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
            },
            "stream": stream,
        }
    
    def _retry_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        stream: bool = False
    ) -> requests.Response:
        """Make request with retry logic."""
        last_error = None
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=self.config.timeout,
                    stream=stream
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Ollama request failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise RuntimeError(f"Ollama request failed after {self.config.max_retries} retries: {last_error}")
    
    def complete(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """Complete a chat conversation."""
        payload = self._make_request(messages, stream=False, **kwargs)
        response = self._retry_request("/api/chat", payload)
        data = response.json()
        
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.config.model),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},  # Ollama doesn't provide
            finish_reason="stop",
            raw_response=data
        )
    
    def stream_complete(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream completion chunks."""
        payload = self._make_request(messages, stream=True, **kwargs)
        response = self._retry_request("/api/chat", payload, stream=True)
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue


def create_client(config: Optional[LLMConfig] = None) -> BaseLLMClient:
    """Factory function to create appropriate LLM client.
    
    Args:
        config: LLMConfig instance. If None, loads from environment.
    
    Returns:
        Appropriate client instance based on provider.
    """
    if config is None:
        config = LLMConfig.from_env()
    
    if config.provider == "ollama":
        return OllamaClient(config)
    else:
        return OpenRouterClient(config)
