"""
title: Grok Manifold^
author: kha1n3vol3
author_url: https://github.com/kha1n3vol3/grok-manifold
funding_url: https://www.starficient.com
version: 0.2
"""

"""
Module: grok_pipe
Description: This module implements a Pipe class for interacting with the Grok API.
It provides functionality to fetch available models, process input messages (text and images),
and handle both streaming and non-streaming API responses. The module uses Pydantic for
configuration management and the requests library for HTTP communication.

Usage:
    Initialize the Pipe class and use its methods to interact with the Grok API:
    >>> pipe = Pipe()
    >>> models = pipe.pipes()
    >>> response = pipe.pipe({"model": "grok-beta", "messages": [{"role": "user", "content": "Hello"}]})
    Note: If GROK_API_KEY is not set, API requests may fail depending on server requirements.
"""

"""
           ████████           
          ████████            
         ████████             
        ████████     █        
       ████████     ███       
      ████████     █████      
     ████████     ███████     
    ████████      ████████    
   ████████        ████████   
  ████████          ████████  
 ████████            ████████ 
████████              ████████
Starficient ^: Above Efficient.
"""

import os
import json
import requests
from typing import List, Union, Generator, Iterator, Optional, Dict
from pydantic import BaseModel, Field
from open_webui.utils.misc import (
    pop_system_message,
)  # Updated import path as per your example


class Pipe:
    """
    A class to manage interactions with the Grok API, including model retrieval and message processing.

    Attributes:
        valves (Pipe.Valves): Configuration settings for API interactions.
        type (str): Type identifier for the pipe.
        id (str): Unique identifier for the pipe instance.
        name (str): Name prefix for the pipe.
    """

    class Valves(BaseModel):
        """
        Configuration model for Grok API interactions using Pydantic.

        Attributes:
            GROK_API_KEY (str): API key for authentication with Grok services (optional).
            GROK_API_BASE_URL (str): Base URL for Grok API endpoints.
            MAX_TOKENS (int): Maximum number of tokens to generate in responses.
            TEMPERATURE (float): Sampling temperature for response generation.
            TOP_P (float): Nucleus sampling top_p value.
            STREAM (bool): Flag to enable streaming responses.
        """

        GROK_API_KEY: str = Field(default="", description="API key for Grok services.")
        GROK_API_BASE_URL: str = Field(
            default="https://api.x.ai/v1",
            description="Base URL for Grok API endpoints.",
        )
        MAX_TOKENS: int = Field(
            default=4096, description="Maximum number of tokens to generate."
        )
        TEMPERATURE: float = Field(default=0.8, description="Sampling temperature.")
        TOP_P: float = Field(default=0.9, description="Nucleus sampling top_p value.")
        STREAM: bool = Field(default=False, description="Whether to stream responses.")

    def __init__(self) -> None:
        """
        Initialize the Pipe instance with configuration from environment variables.
        """
        self.valves = self.Valves(
            GROK_API_KEY=os.getenv("GROK_API_KEY", ""),
            GROK_API_BASE_URL=os.getenv("GROK_API_BASE_URL", "https://api.x.ai/v1"),
        )
        self.type = "manifold"
        self.id = "grok"
        self.name = "grok/"
        self.session = requests.Session()  # Reusable session for HTTP requests

    def get_model_id(self, model_name: str) -> str:
        """
        Extract the base model name from a potentially formatted string.

        Args:
            model_name (str): The model name, possibly including prefixes or separators.

        Returns:
            str: The base model name (e.g., "grok-beta" from "prefix/grok-beta").

        Example:
            >>> pipe = Pipe()
            >>> pipe.get_model_id("xai.grok-beta")
            'grok-beta'
        """
        parts = model_name.replace(".", "/").split("/")
        return parts[-1] if parts else ""

    def get_grok_models(self) -> List[Dict[str, str]]:
        """
        Fetch available models from the Grok API.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing model IDs and names,
                                 empty if the request fails.

        Example:
            >>> pipe = Pipe()
            >>> models = pipe.get_grok_models()
            >>> print(models)
            [{'id': 'grok-beta', 'name': 'grok-beta'}, ...]
        """
        headers = {
            "Authorization": f"Bearer {self.valves.GROK_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            response = self.session.get(
                f"{self.valves.GROK_API_BASE_URL}/models", headers=headers, timeout=10
            )
            response.raise_for_status()
            models_data = response.json()
            return [
                {"id": model["id"], "name": model["id"]}
                for model in models_data.get("data", [])
            ]
        except requests.RequestException as e:
            print(f"Error fetching models: {e}")
            return []

    def pipes(self) -> List[Dict[str, str]]:
        """
        Retrieve the list of available Grok models.

        Returns:
            List[Dict[str, str]]: A list of model information dictionaries.
        """
        return self.get_grok_models()

    def process_image(
        self, image_data: Dict[str, Dict[str, str]]
    ) -> Dict[str, Union[str, Dict]]:
        """
        Process image data into a format suitable for the Grok API.

        Args:
            image_data (Dict[str, Dict[str, str]]): Image data containing a URL or base64 string.

        Returns:
            Dict[str, Union[str, Dict]]: Processed image data in API-compatible format,
                                        empty dict if processing fails.

        Example:
            >>> pipe = Pipe()
            >>> image = {"image_url": {"url": "data:image/png;base64,abc123"}}
            >>> pipe.process_image(image)
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': 'abc123'}}
        """
        try:
            url = image_data.get("image_url", {}).get("url", "")
            if not url:
                return {}
            if url.startswith("data:image"):
                mime_type, base64_data = url.split(",", 1)
                media_type = mime_type.split(":")[1].split(";")[0]
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data,
                    },
                }
            return {
                "type": "image",
                "source": {"type": "url", "url": url},
            }
        except (ValueError, IndexError):
            return {}

    def pipe(self, body: Dict) -> Union[str, Generator, Iterator]:
        """
        Process input messages and interact with the Grok API.

        Args:
            body (Dict): Request body containing model, messages, and optional parameters.

        Returns:
            Union[str, Generator, Iterator]: Response content (string for non-streaming,
                                            generator/iterator for streaming), or error message.

        Example:
            >>> pipe = Pipe()
            >>> body = {"model": "grok-beta", "messages": [{"role": "user", "content": "Hi"}]}
            >>> response = pipe.pipe(body)
            'Hello there!'
        """
        system_message, messages = pop_system_message(body.get("messages", []))
        processed_messages: List[Dict[str, str]] = []

        for message in messages:
            if not isinstance(message, dict) or "role" not in message:
                continue
            if isinstance(message.get("content"), list):
                for item in message["content"]:
                    if item.get("type") == "text" and item.get("text"):
                        processed_messages.append(
                            {"role": message["role"], "content": item["text"]}
                        )
                    elif item.get("type") == "image_url":
                        processed_image = self.process_image(item)
                        if processed_image:
                            processed_messages.append(processed_image)
            elif message.get("content"):
                processed_messages.append(
                    {"role": message["role"], "content": str(message["content"])}
                )

        if system_message:
            processed_messages.insert(
                0, {"role": "system", "content": str(system_message)}
            )

        model_id = self.get_model_id(body.get("model", ""))
        payload = {
            "model": model_id,
            "messages": processed_messages,
            "stream": body.get("stream", self.valves.STREAM),
            "temperature": body.get("temperature", self.valves.TEMPERATURE),
            "max_tokens": body.get("max_tokens", self.valves.MAX_TOKENS),
            "top_p": body.get("top_p", self.valves.TOP_P),
            "frequency_penalty": body.get("frequency_penalty", 0),
            "presence_penalty": body.get("presence_penalty", 0),
            "stop": body.get("stop", []),
            "user": body.get("user", ""),
            "n": body.get("n", 1),
            "logprobs": body.get("logprobs", False),
            "top_logprobs": body.get("top_logprobs", 0),
        }

        headers = {
            "Authorization": f"Bearer {self.valves.GROK_API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{self.valves.GROK_API_BASE_URL}/chat/completions"

        try:
            if payload["stream"]:
                return self.stream_response(url, headers, payload)
            return self.non_stream_response(url, headers, payload)
        except requests.RequestException as e:
            print(f"Error in pipe method: {e}")
            return f"Error: {e}"

    def stream_response(
        self, url: str, headers: Dict[str, str], payload: Dict
    ) -> Generator[str, None, None]:
        """
        Handle streaming responses from the Grok API.

        Args:
            url (str): API endpoint URL.
            headers (Dict[str, str]): HTTP headers for the request.
            payload (Dict): Request payload.

        Yields:
            str: Incremental content from the streaming response.

        Example:
            >>> pipe = Pipe()
            >>> body = {"model": "grok-beta", "messages": [{"role": "user", "content": "Hi"}], "stream": True}
            >>> for chunk in pipe.pipe(body):
            ...     print(chunk, end='')
            Hello there!
        """
        with self.session.post(
            url, headers=headers, json=payload, stream=True, timeout=30
        ) as response:
            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get("choices") and "delta" in data["choices"][0]:
                                content = data["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON: {e}")
                            continue

    def non_stream_response(
        self, url: str, headers: Dict[str, str], payload: Dict
    ) -> str:
        """
        Handle non-streaming responses from the Grok API.

        Args:
            url (str): API endpoint URL.
            headers (Dict[str, str]): HTTP headers for the request.
            payload (Dict): Request payload.

        Returns:
            str: The complete response content, or an error message if the request fails.
        """
        response = self.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")
        res = response.json()
        return res["choices"][0]["message"]["content"] if res.get("choices") else ""


if __name__ == "__main__":
    # Example usage
    pipe = Pipe()
    body = {"model": "grok-beta", "messages": [{"role": "user", "content": "Hello"}]}
    response = pipe.pipe(body)
    print(response)
