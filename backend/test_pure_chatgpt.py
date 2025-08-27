#!/usr/bin/env python3
"""Quick test for Pure ChatGPT Integration"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv(".env")

async def test_pure_chatgpt():
    """Test pure ChatGPT response"""
    from pure_chatgpt import get_pure_chatgpt_response
    
    print("🤖 Testing Pure ChatGPT Integration")
    print("=" * 60)
    
    query = "كيف يمكنني تأسيس شركة استثمار أجنبي في السعودية؟"
    print(f"📝 Query: {query}")
    print("-" * 60)
    
    try:
        response = await get_pure_chatgpt_response(query)
        
        print("✅ Response received!")
        print(f"📊 Length: {len(response)} characters, {len(response.split())} words")
        print("-" * 60)
        print("📄 Response:")
        print(response)
        print("-" * 60)
        
        # Check for ChatGPT characteristics
        has_formatting = any(marker in response for marker in ["##", "**", "*", ">", "1.", "•"])
        has_emojis = any(char in response for char in "🔥⭐📊💡🚀✅❌⚠️")
        is_comprehensive = len(response.split()) > 300
        
        print("🔍 Analysis:")
        print(f"  - Rich formatting: {'✅' if has_formatting else '❌'}")
        print(f"  - Emojis present: {'✅' if has_emojis else '❌'}")
        print(f"  - Comprehensive (>300 words): {'✅' if is_comprehensive else '❌'}")
        
        if has_formatting and is_comprehensive:
            print("🎉 SUCCESS: Response looks like ChatGPT!")
        else:
            print("⚠️ WARNING: Response doesn't match ChatGPT style")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pure_chatgpt())