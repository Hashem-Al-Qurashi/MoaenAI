"""
Ultimate ChatGPT Clone - Multiple Strategies to Match ChatGPT.com
"""
from openai import AsyncOpenAI
import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

class UltimateChatGPTClone:
    """
    Multiple strategies to exactly match ChatGPT.com responses
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def strategy_1_pure_gpt4(self, message: str, history: List[Dict] = None) -> str:
        """Strategy 1: Pure GPT-4 with NO system prompt"""
        messages = []
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    async def strategy_2_chatgpt_prompt(self, message: str, history: List[Dict] = None) -> str:
        """Strategy 2: With ChatGPT.com's likely minimal prompt"""
        messages = [
            {"role": "system", "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as helpfully as possible."}
        ]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    async def strategy_3_localized(self, message: str, history: List[Dict] = None) -> str:
        """Strategy 3: With location awareness (Saudi Arabia)"""
        # Detect if question is about Saudi topics
        saudi_keywords = ['السعودية', 'سعودي', 'المملكة', 'الرياض', 'استثمار أجنبي', 'شركة']
        is_saudi_topic = any(keyword in message for keyword in saudi_keywords)
        
        messages = []
        if is_saudi_topic:
            # Add context about Saudi regulations
            messages.append({
                "role": "system", 
                "content": "Provide detailed, practical information about Saudi Arabian regulations and procedures when relevant."
            })
        
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    async def strategy_4_gpt4_turbo(self, message: str, history: List[Dict] = None) -> str:
        """Strategy 4: GPT-4-Turbo (faster, might be what ChatGPT Plus uses)"""
        messages = []
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    async def strategy_5_exact_params(self, message: str, history: List[Dict] = None) -> str:
        """Strategy 5: Exact ChatGPT.com parameters (discovered through testing)"""
        messages = []
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=1.0,  # ChatGPT.com default
            max_tokens=4096,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    
    async def compare_all_strategies(self, message: str) -> Dict[str, str]:
        """Compare all strategies to see which matches ChatGPT.com best"""
        results = {}
        
        print("Testing all strategies...")
        
        # Test each strategy
        strategies = [
            ("Pure GPT-4", self.strategy_1_pure_gpt4),
            ("ChatGPT Prompt", self.strategy_2_chatgpt_prompt),
            ("Localized", self.strategy_3_localized),
            ("GPT-4 Turbo", self.strategy_4_gpt4_turbo),
            ("Exact Params", self.strategy_5_exact_params)
        ]
        
        for name, strategy in strategies:
            try:
                print(f"Testing {name}...")
                response = await strategy(message)
                results[name] = response
                print(f"✓ {name} completed")
            except Exception as e:
                results[name] = f"Error: {str(e)}"
                print(f"✗ {name} failed: {e}")
        
        return results


# FastAPI integration
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

router = APIRouter()

class CloneRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    strategy: Optional[str] = "pure_gpt4"  # default strategy

ultimate_clone = UltimateChatGPTClone()

@router.post("/ultimate-chatgpt")
async def ultimate_chatgpt_endpoint(request: CloneRequest):
    """
    Ultimate ChatGPT clone with multiple strategies
    """
    try:
        # Select strategy
        strategy_map = {
            "pure_gpt4": ultimate_clone.strategy_1_pure_gpt4,
            "chatgpt_prompt": ultimate_clone.strategy_2_chatgpt_prompt,
            "localized": ultimate_clone.strategy_3_localized,
            "gpt4_turbo": ultimate_clone.strategy_4_gpt4_turbo,
            "exact_params": ultimate_clone.strategy_5_exact_params
        }
        
        strategy_func = strategy_map.get(request.strategy, ultimate_clone.strategy_1_pure_gpt4)
        response = await strategy_func(request.message, request.history)
        
        return {
            "response": response,
            "strategy": request.strategy,
            "model": "gpt-4",
            "type": "ultimate_chatgpt_clone"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare-strategies")
async def compare_strategies_endpoint(request: CloneRequest):
    """
    Compare all strategies to find which matches ChatGPT.com
    """
    try:
        results = await ultimate_clone.compare_all_strategies(request.message)
        return {
            "question": request.message,
            "strategies": results,
            "recommendation": "Compare these with ChatGPT.com to find the best match"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Test script
    async def test():
        from dotenv import load_dotenv
        load_dotenv()
        
        clone = UltimateChatGPTClone()
        
        question = "كيفية تأسيس شركة استثمار أجنبي في السعودية؟"
        
        print(f"Testing question: {question}\n")
        print("=" * 80)
        
        results = await clone.compare_all_strategies(question)
        
        for strategy, response in results.items():
            print(f"\n{'='*80}")
            print(f"STRATEGY: {strategy}")
            print(f"{'='*80}")
            print(response[:500] + "..." if len(response) > 500 else response)
        
        print("\n" + "="*80)
        print("Compare these responses with ChatGPT.com to find the best match!")
    
    asyncio.run(test())