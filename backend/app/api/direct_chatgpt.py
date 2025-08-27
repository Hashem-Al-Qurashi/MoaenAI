"""
Direct ChatGPT API - Completely bypasses all systems
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv(".env")

router = APIRouter()

class DirectChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

# Direct OpenAI client - no middleware
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/direct-chatgpt")
async def direct_chatgpt_endpoint(request: DirectChatRequest):
    """
    Direct ChatGPT endpoint - bypasses ALL systems
    """
    try:
        # Build messages for pure ChatGPT - NO SYSTEM PROMPT
        messages = []
        
        # Add history
        for msg in request.history[-10:]:
            messages.append(msg)
        
        # Add current message
        messages.append({
            "role": "user", 
            "content": request.message
        })
        
        # Pure ChatGPT API call - EXACT same as chatgpt.com
        response = await openai_client.chat.completions.create(
            model="gpt-4",  # Latest GPT-4 model same as ChatGPT Plus
            messages=messages,
            temperature=0.7,         # ChatGPT.com default for balanced responses
            max_tokens=4096,         
            top_p=1.0,              
            frequency_penalty=0,     
            presence_penalty=0,      
            stream=False
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": "pure-chatgpt",
            "pure_chatgpt": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/direct-chatgpt-stream")  
async def direct_chatgpt_stream(request: DirectChatRequest):
    """
    Direct ChatGPT streaming - bypasses ALL systems
    """
    async def stream_response():
        try:
            # Build messages for pure ChatGPT - NO SYSTEM PROMPT
            messages = []
            
            # Add history
            for msg in request.history[-10:]:
                messages.append(msg)
            
            # Add current message
            messages.append({
                "role": "user",
                "content": request.message
            })
            
            # Stream pure ChatGPT
            stream = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                temperature=1.0,         # ChatGPT default
                max_tokens=4096,         # ChatGPT default
                top_p=1.0,              # ChatGPT default
                frequency_penalty=0,     # ChatGPT default
                presence_penalty=0,      # ChatGPT default
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'content': content})}\n\n"
                    
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )