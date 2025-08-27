#!/usr/bin/env python3
"""Test Direct ChatGPT API - Complete Bypass"""

import asyncio
import aiohttp
import json

async def test_direct_chatgpt():
    """Test the direct ChatGPT endpoint"""
    print("🚀 Testing Direct ChatGPT API (Complete Bypass)")
    print("=" * 70)
    
    url = "http://localhost:8000/api/direct-chatgpt"
    data = {
        "message": "كيف يمكنني تأسيس شركة استثمار أجنبي في السعودية؟",
        "history": []
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    chatgpt_response = result["response"]
                    
                    print("✅ Direct ChatGPT API Response Received!")
                    print(f"📊 Length: {len(chatgpt_response)} characters, {len(chatgpt_response.split())} words")
                    print(f"🔧 Model: {result.get('model', 'unknown')}")
                    print(f"🚀 Bypassed all systems: {result.get('bypassed_all_systems', False)}")
                    print("-" * 70)
                    print("📄 Response:")
                    print(chatgpt_response)
                    print("-" * 70)
                    
                    # Analyze ChatGPT characteristics
                    has_headers = "##" in chatgpt_response
                    has_bold = "**" in chatgpt_response
                    has_bullets = any(marker in chatgpt_response for marker in ["•", "-", "*"])
                    has_emojis = any(char in chatgpt_response for char in "🔥⭐📊💡🚀✅❌⚠️💼📋📝")
                    is_comprehensive = len(chatgpt_response.split()) > 400
                    
                    print("🔍 ChatGPT Style Analysis:")
                    print(f"  - Headers (##): {'✅' if has_headers else '❌'}")
                    print(f"  - Bold text (**): {'✅' if has_bold else '❌'}")
                    print(f"  - Bullet points: {'✅' if has_bullets else '❌'}")
                    print(f"  - Emojis: {'✅' if has_emojis else '❌'}")
                    print(f"  - Comprehensive (>400 words): {'✅' if is_comprehensive else '❌'}")
                    
                    score = sum([has_headers, has_bold, has_bullets, has_emojis, is_comprehensive])
                    print(f"📊 ChatGPT Style Score: {score}/5")
                    
                    if score >= 4:
                        print("🎉 SUCCESS: This looks like real ChatGPT!")
                    elif score >= 2:
                        print("⚠️ PARTIAL: Getting there but needs improvement")
                    else:
                        print("❌ FAIL: Still doesn't look like ChatGPT")
                        
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        print("Make sure backend server is running on port 8000")

if __name__ == "__main__":
    asyncio.run(test_direct_chatgpt())