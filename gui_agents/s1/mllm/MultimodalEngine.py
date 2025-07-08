# Author: Saaket Agashe
# Date: 2021-09-15
# License: MIT

import os
import re
import time
import threading
from io import BytesIO
from typing import Optional

import backoff
import numpy as np
import openai
import requests
from anthropic import Anthropic
from openai import APIConnectionError, APIError, AzureOpenAI, OpenAI, RateLimitError
from PIL import Image

try:
    from groq import Groq  # type: ignore
except ImportError:
    Groq = None

# TODO: Import only if module exists, else ignore
# from llava.model.builder import load_pretrained_model
# from llava.mm_utils import (
#     process_images,
#     tokenizer_image_token,
#     get_model_name_from_path,
#     KeywordsStoppingCriteria,
# )
# from llava.constants import (
#     IMAGE_TOKEN_INDEX,
#     DEFAULT_IMAGE_TOKEN,
#     DEFAULT_IM_START_TOKEN,
#     DEFAULT_IM_END_TOKEN,
#     IMAGE_PLACEHOLDER,
# )
# from llava.conversation import conv_templates, SeparatorStyle


# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def image_parser(args):
    out = args.image_file.split(args.sep)
    return out


def load_image(image_file):
    if image_file.startswith("http") or image_file.startswith("https"):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        image = Image.open(image_file).convert("RGB")
    return image


def load_images(image_files):
    out = []
    for image_file in image_files:
        image = load_image(image_file)
        out.append(image)
    return out


class LMMEngine:
    pass


class LMMEngineOpenAI(LMMEngine):
    def __init__(self, api_key=None, model=None, rate_limit=-1, **kwargs):
        assert model is not None, "model must be provided"
        self.model = model

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "An API Key needs to be provided in either the api_key parameter or as an environment variable named OPENAI_API_KEY"
            )

        self.api_key = api_key
        self.request_interval = 0 if rate_limit == -1 else 60.0 / rate_limit

        self.llm_client = OpenAI(api_key=self.api_key)

    @backoff.on_exception(
        backoff.expo, (APIConnectionError, APIError, RateLimitError), max_time=60
    )
    def generate(self, messages, temperature=0.0, max_new_tokens=None, **kwargs):
        """Generate the next message based on previous messages"""
        return (
            self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_new_tokens if max_new_tokens else 4096,
                temperature=temperature,
                **kwargs,
            )
            .choices[0]
            .message.content
        )


class LMMEngineAnthropic(LMMEngine):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API Key is required. Please set the ANTHROPIC_API_KEY environment variable or pass it as a parameter.\n"
                "You can get an API key from: https://console.anthropic.com/"
            )
        
        self.api_key = api_key
        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    @backoff.on_exception(
        backoff.expo, (APIConnectionError, APIError, RateLimitError), max_time=60
    )
    def generate(self, messages, temperature=0.0, max_new_tokens=None, **kwargs):
        """Generate the next message based on previous messages"""
        return (
            self.client.messages.create(
                system=messages[0]["content"][0]["text"],
                model=self.model,
                messages=messages[1:],
                max_tokens=max_new_tokens if max_new_tokens else 4096,
                temperature=temperature,
                **kwargs,
            )
            .content[0]
            .text
        )


class OpenAIEmbeddingEngine(LMMEngine):
    def __init__(
        self,
        api_key=None,
        rate_limit: int = -1,
        display_cost: bool = True,
    ):
        """Init an OpenAI Embedding engine

        Args:
            api_key (_type_, optional): Auth key from OpenAI. Defaults to None.
            rate_limit (int, optional): Max number of requests per minute. Defaults to -1.
            display_cost (bool, optional): Display cost of API call. Defaults to True.
        """
        self.model = "text-embedding-3-small"
        self.cost_per_thousand_tokens = 0.00002

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "An API Key needs to be provided in either the api_key parameter or as an environment variable named OPENAI_API_KEY"
            )
        self.api_key = api_key
        self.display_cost = display_cost
        self.request_interval = 0 if rate_limit == -1 else 60.0 / rate_limit

    @backoff.on_exception(
        backoff.expo,
        (
            APIError,
            RateLimitError,
            APIConnectionError,
        ),
    )
    def get_embeddings(self, text: str) -> np.ndarray:
        client = OpenAI(api_key=self.api_key)
        response = client.embeddings.create(model=self.model, input=text)
        if self.display_cost:
            total_tokens = response.usage.total_tokens
            cost = self.cost_per_thousand_tokens * total_tokens / 1000
            # print(f"Total cost for this embedding API call: {cost}")
        return np.array([data.embedding for data in response.data])


class LMMEngineAzureOpenAI(LMMEngine):
    def __init__(
        self,
        api_key=None,
        azure_endpoint=None,
        model=None,
        api_version=None,
        rate_limit=-1,
        **kwargs
    ):
        assert model is not None, "model must be provided"
        self.model = model

        assert api_version is not None, "api_version must be provided"
        self.api_version = api_version

        api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "An API Key needs to be provided in either the api_key parameter or as an environment variable named AZURE_OPENAI_API_KEY"
            )

        self.api_key = api_key

        azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_API_BASE")
        if azure_endpoint is None:
            raise ValueError(
                "An Azure API endpoint needs to be provided in either the azure_endpoint parameter or as an environment variable named AZURE_OPENAI_API_BASE"
            )

        self.azure_endpoint = azure_endpoint
        self.request_interval = 0 if rate_limit == -1 else 60.0 / rate_limit

        self.llm_client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )
        self.cost = 0.0

    # @backoff.on_exception(backoff.expo, (APIConnectionError, APIError, RateLimitError), max_tries=10)
    def generate(self, messages, temperature=0.0, max_new_tokens=None, **kwargs):
        """Generate the next message based on previous messages"""
        completion = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_new_tokens if max_new_tokens else 4096,
            temperature=temperature,
            **kwargs,
        )
        total_tokens = completion.usage.total_tokens
        self.cost += 0.02 * ((total_tokens + 500) / 1000)
        return completion.choices[0].message.content


class LMMEnginevLLM(LMMEngine):
    def __init__(
        self, base_url=None, api_key=None, model=None, rate_limit=-1, **kwargs
    ):
        """Initialize a vLLM/Ollama engine.

        If no base_url is supplied and no vLLM_ENDPOINT_URL environment variable is
        set, we *assume* the user is running an Ollama server locally and default
        to `http://localhost:11434/v1` – the OpenAI-compatible endpoint exposed
        by Ollama. This allows passing `--engine-type vllm` for local Ollama
        models without any additional configuration.

        Likewise, if no api_key is supplied we set a dummy key ("ollama") so the
        OpenAI python client does not complain about a missing key.
        """

        assert model is not None, "model must be provided"
        self.model = model

        # Provide sensible defaults for local Ollama setups
        self.base_url = (
            base_url
            or os.getenv("vLLM_ENDPOINT_URL")
            or os.getenv("VLLM_ENDPOINT_URL")
            or "http://localhost:11434/v1"
        )

        # OpenAI client insists on an api_key – use a placeholder if not supplied
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "ollama")

        # Rate limiting configuration (requests per minute)
        self.request_interval = 0 if rate_limit == -1 else 60.0 / rate_limit

        # Instantiate OpenAI-compatible client pointed at the local/vLLM endpoint
        self.llm_client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    # @backoff.on_exception(backoff.expo, (APIConnectionError, APIError, RateLimitError), max_tries=10)
    # TODO: Default params chosen for the Qwen model
    def generate(
        self,
        messages,
        temperature=0.0,
        top_p=0.8,
        repetition_penalty=1.05,
        max_new_tokens=512,
        **kwargs
    ):
        """Generate the next message based on previous messages"""
        try:
            completion = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_new_tokens if max_new_tokens else 4096,
                temperature=temperature,
                top_p=top_p,
                extra_body={"repetition_penalty": repetition_penalty},
            )
            return completion.choices[0].message.content
        except APIError as e:
            # Common case with Ollama: model has not been pulled yet
            if getattr(e, "code", "") == "model_not_found":
                raise RuntimeError(
                    f"Ollama did not recognise the model '{self.model}'. "
                    "Run `ollama list` to see available models or pull it with "
                    f"`ollama pull {self.model}` before retrying."
                ) from e
            raise


class LMMEngineGroq(LMMEngine):
    """LLM Engine for Groq Cloud models using the OpenAI-compatible REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-8b-instant",
        **kwargs,  # Accept and ignore additional parameters like engine_type
    ):
        if Groq is None:
            raise ImportError(
                "Groq library not installed. Please install it with: pip install groq"
            )
            
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Groq API Key is required. Please set the GROQ_API_KEY environment variable or pass it as a parameter.\n"
                "You can get an API key from: https://console.groq.com/keys"
            )
        
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=self.api_key)

    @backoff.on_exception(
        backoff.expo, (APIConnectionError, APIError, RateLimitError), max_time=60
    )
    def generate(self, messages, temperature: float = 0.0, max_new_tokens: int | None = None, **kwargs):
        """Generate the next message based on previous messages"""
        return (
            self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_new_tokens if max_new_tokens else 4096,
                temperature=temperature,
                **kwargs,
            )
            .choices[0]
            .message.content
        )


class LMMEngineOllama(LMMEngine):
    """LLM Engine for Ollama local models using the native Ollama Python client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "llama3.2-vision",
        **kwargs,  # Accept and ignore additional parameters like engine_type
    ):
        """Initialize Ollama engine.
        
        Args:
            base_url: Ollama server URL (defaults to http://localhost:11434)
            api_key: Not used for Ollama but kept for compatibility
            model: Model name (e.g., "llama3.2-vision:latest")
        """
        try:
            # Import using the exact same pattern as the working test
            from ollama import chat
            self.ollama_chat = chat
        except ImportError:
            raise ImportError(
                "Ollama library not installed. Please install it with: pip install ollama"
            )
        
        self.model = model
        
        print(f"Ollama engine initialized:")
        print(f"  Model: {self.model}")
        print(f"  Using chat function directly")

    def generate(self, messages, temperature: float = 0.0, max_new_tokens: int | None = None, **kwargs):
        """Generate the next message based on previous messages using Ollama chat API"""
        try:
            # Convert messages to Ollama chat format and clean them
            chat_messages = self._convert_to_chat_messages(messages)
            
            # Use the exact same calling pattern as the working test
            response = self.ollama_chat(
                model=self.model,
                messages=chat_messages
            )
            
            # Extract content using the same pattern as working test
            return response['message']['content']
            
        except Exception as e:
            # Handle common Ollama errors with helpful messages
            error_msg = str(e).lower()
            
            if "model" in error_msg and ("not found" in error_msg or "does not exist" in error_msg):
                raise RuntimeError(
                    f"Model '{self.model}' not found in Ollama.\n"
                    f"Try: ollama pull {self.model}\n"
                    f"Original error: {e}"
                ) from e
            elif "connection" in error_msg or "disconnected" in error_msg or "failed to connect" in error_msg:
                raise RuntimeError(
                    f"Cannot connect to Ollama server.\n"
                    f"Make sure Ollama is running and try again.\n"
                    f"Original error: {e}"
                ) from e
            else:
                raise RuntimeError(f"Ollama error: {e}") from e

    def _convert_to_chat_messages(self, messages):
        """Convert OpenAI-style messages to Ollama chat format, filtering out invalid content"""
        chat_messages = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            # Skip invalid roles
            if role not in ["system", "user", "assistant"]:
                continue
            
            # Handle both string and list content formats
            if isinstance(content, list):
                # Extract text from multimodal content, skip images for now
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                content = "\n".join(text_parts)
            
            # Skip empty content
            if not content or not content.strip():
                continue
            
            # Add to chat messages in Ollama format (same as working test)
            chat_messages.append({
                "role": role,
                "content": content.strip()
            })
        
        return chat_messages
