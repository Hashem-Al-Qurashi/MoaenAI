"""
Pure ChatGPT Integration - Exactly like ChatGPT.com
"""

import os
from typing import AsyncIterator, List, Dict, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv(".env")

class PureChatGPT:
    """Direct ChatGPT integration - exactly like chatgpt.com"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        self.client = AsyncOpenAI(api_key=api_key)
        # Use GPT-3.5-turbo-16k for now (faster and more reliable)
        # Can upgrade to GPT-4 later if needed
        self.model = "gpt-3.5-turbo-16k"
        
    async def chat(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Direct ChatGPT call - exactly like chatgpt.com
        """
        try:
            messages = []
            
            # NO SYSTEM PROMPT - Pure ChatGPT like chatgpt.com
            
            # Add conversation history if exists
            if conversation_history:
                for msg in conversation_history[-20:]:  # Keep more history like ChatGPT
                    if msg.get("role") and msg.get("content"):
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Call ChatGPT with same parameters as chatgpt.com
            if stream:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=1.0,  # ChatGPT default
                    max_tokens=4096,  # Maximum like ChatGPT Plus
                    top_p=1.0,        # ChatGPT default
                    frequency_penalty=0,  # ChatGPT default
                    presence_penalty=0,   # ChatGPT default
                    stream=True
                )
                
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=1.0,
                    max_tokens=4096,
                    top_p=1.0,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stream=False
                )
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"ChatGPT error: {e}")
            yield f"Error: {str(e)}"

# Global instance
pure_chatgpt = PureChatGPT()

async def get_pure_chatgpt_response(
    query: str, 
    history: List[Dict[str, str]] = None
) -> str:
    """Get complete ChatGPT response (non-streaming)"""
    chunks = []
    async for chunk in pure_chatgpt.chat(query, history, stream=False):
        chunks.append(chunk)
    return ''.join(chunks)

async def stream_pure_chatgpt_response(
    query: str,
    history: List[Dict[str, str]] = None  
) -> AsyncIterator[str]:
    """Stream ChatGPT response"""
    async for chunk in pure_chatgpt.chat(query, history, stream=True):
        yield chunk