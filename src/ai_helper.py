"""
AI Helper module for integrating Google's Gemini 2.0 model into the MUD game.
This module provides a base class for AI-powered functionalities.
"""

import os
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from google import genai

class GeminiHelper:
    """Base class for Gemini 2.0 AI integration."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Gemini AI helper.
        
        Args:
            api_key: Google AI API key. If not provided, will try to get from GOOGLE_API_KEY env variable.
            model_id: The model ID to use. Defaults to gemini-2.0-flash-exp.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass it directly.")
        
        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = model_id
        self.session = None
        
    async def start_session(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Start a new live session with optional configuration.
        
        Args:
            config: Optional configuration for the session.
        """
        default_config = {"response_modalities": ["TEXT"]}
        session_config = config or default_config
        
        self.session = await self.client.aio.live.connect(
            model=self.model_id,
            config=session_config
        ).__aenter__()
        
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response using the Gemini model.
        
        Args:
            prompt: The input prompt for the model
            context: Optional additional context as a dictionary
            
        Returns:
            str: The generated response
        """
        try:
            # Format the prompt with context if provided
            formatted_prompt = f"{prompt}\nContext: {context}" if context else prompt
            
            # For simple one-off responses without a session
            response = await self.client.models.generate_content(
                model=self.model_id,
                contents=formatted_prompt
            )
            return response.text
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
            
    async def chat_response(self, message: str) -> AsyncGenerator[str, None]:
        """
        Send a message in chat mode and yield responses as they come.
        
        Args:
            message: The message to send
            
        Yields:
            Streamed responses from the model
        """
        if not self.session:
            await self.start_session()
            
        try:
            await self.session.send(message, end_of_turn=True)
            async for response in self.session.receive():
                yield response.text
                
        except Exception as e:
            yield f"Error in chat response: {str(e)}"
            
    async def close_session(self) -> None:
        """Close the current session if one exists."""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None 