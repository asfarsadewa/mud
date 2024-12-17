"""
AI Helper module for integrating Google's Gemini 2.0 model into the MUD game.
This module provides a base class for AI-powered functionalities.
"""

import os
from typing import Optional, Dict, Any
from google import genai

class GeminiHelper:
    """Base class for Gemini 2.0 AI integration."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-2.0-flash-exp"):
        """Initialize the Gemini AI helper."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass it directly.")
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = model_id
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {str(e)}")
        
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response using the Gemini model."""
        try:
            # Prepare the prompt with context if provided
            full_prompt = prompt
            if context:
                context_str = "\nContext:\n" + "\n".join(f"{k}: {v}" for k, v in context.items())
                full_prompt += context_str
                
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt
            )
            
            if not response or not response.text:
                return prompt
                
            response_text = response.text.strip()
            if not response_text or response_text == full_prompt:
                return prompt
                
            return response_text
            
        except Exception:
            return prompt
            
    async def close_session(self) -> None:
        """Placeholder for compatibility."""
        pass