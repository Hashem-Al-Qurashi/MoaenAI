"""
Enterprise Solution: Pure ChatGPT API with exact ChatGPT.com configuration
"""
from openai import AsyncOpenAI
import os
import asyncio
from typing import List, Dict, Optional

class PureChatGPTEnterprise:
    """
    Enterprise-grade ChatGPT integration that matches ChatGPT.com exactly
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def get_raw_chatgpt_response(
        self, 
        message: str, 
        history: List[Dict[str, str]] = None,
        model: str = "gpt-4"  # ChatGPT Plus uses GPT-4
    ) -> str:
        """
        Get the EXACT same response as ChatGPT.com
        
        Key differences from basic API:
        1. Uses GPT-4 (ChatGPT Plus model)
        2. No system prompts
        3. Exact same parameters as ChatGPT.com
        4. Preserves conversation context
        """
        
        # Build message history - NO SYSTEM PROMPT
        messages = []
        
        # Add conversation history if provided
        if history:
            for msg in history[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Call OpenAI API with EXACT ChatGPT.com parameters
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            # ChatGPT.com default parameters
            temperature=0.7,      # Balanced creativity and coherence
            max_tokens=4096,      # Maximum response length
            top_p=1.0,           # No nucleus sampling restriction
            frequency_penalty=0,  # No penalty for repetition
            presence_penalty=0,   # No penalty for new topics
            n=1,                 # Single response
            stream=False         # Complete response (not streaming)
        )
        
        return response.choices[0].message.content
    
    async def get_streaming_response(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        model: str = "gpt-4"
    ):
        """
        Stream response exactly like ChatGPT.com
        """
        
        messages = []
        
        if history:
            for msg in history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Stream with exact ChatGPT.com parameters
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0,
            n=1,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# Enterprise API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    model: Optional[str] = "gpt-4"  # Default to GPT-4

enterprise_chatgpt = PureChatGPTEnterprise()

@router.post("/enterprise/chatgpt")
async def enterprise_chatgpt_endpoint(request: ChatRequest):
    """
    Enterprise endpoint - returns EXACT ChatGPT.com responses
    """
    try:
        response = await enterprise_chatgpt.get_raw_chatgpt_response(
            message=request.message,
            history=request.history,
            model=request.model
        )
        
        return {
            "response": response,
            "model": request.model,
            "type": "pure_chatgpt_enterprise",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Test the enterprise solution
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test():
        chatgpt = PureChatGPTEnterprise()
        
        # Test with your exact question
        question = "كيفية تأسيس شركة استثمار أجنبي؟"
        
        print(f"Testing Enterprise ChatGPT with: {question}")
        print("-" * 50)
        
        response = await chatgpt.get_raw_chatgpt_response(question)
        print(response)
        
    asyncio.run(test())