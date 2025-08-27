#!/usr/bin/env python3
"""Compare both endpoints to see which one you're actually using"""

import asyncio
import aiohttp
import json

async def test_both_endpoints():
    """Test both endpoints and compare responses"""
    print("🔍 COMPARING BOTH ENDPOINTS")
    print("=" * 80)
    
    query = "كيف يمكنني تأسيس شركة استثمار أجنبي في السعودية؟"
    
    # Test 1: Direct ChatGPT endpoint
    print("1️⃣ Testing DIRECT CHATGPT endpoint (/api/direct-chatgpt)")
    print("-" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            url1 = "http://localhost:8000/api/direct-chatgpt"
            data1 = {"message": query, "history": []}
            
            async with session.post(url1, json=data1) as response:
                if response.status == 200:
                    result1 = await response.json()
                    direct_response = result1["response"]
                    
                    print(f"✅ Status: {response.status}")
                    print(f"📊 Length: {len(direct_response)} chars, {len(direct_response.split())} words")
                    print("📄 Response preview (first 200 chars):")
                    print(direct_response[:200] + "...")
                    
                    # Check ChatGPT features
                    has_emojis = any(char in direct_response for char in "🌟🚀✅📊💡⚠️🎉")
                    has_headers = "##" in direct_response
                    has_bold = "**" in direct_response
                    
                    print(f"🔍 ChatGPT Features: Emojis:{has_emojis} Headers:{has_headers} Bold:{has_bold}")
                else:
                    print(f"❌ Failed: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    
    # Test 2: Original chat endpoint (what frontend uses)
    print("2️⃣ Testing ORIGINAL CHAT endpoint (/api/chat/message)")
    print("-" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            url2 = "http://localhost:8000/api/chat/message"
            form_data = aiohttp.FormData()
            form_data.add_field('message', query)
            form_data.add_field('session_id', 'test_session_123')
            
            async with session.post(url2, data=form_data) as response:
                if response.status == 200:
                    result2 = await response.json()
                    original_response = result2.get("ai_message", {}).get("content", "No content found")
                    
                    print(f"✅ Status: {response.status}")
                    print(f"📊 Length: {len(original_response)} chars, {len(original_response.split())} words")
                    print("📄 Response preview (first 200 chars):")
                    print(original_response[:200] + "...")
                    
                    # Check ChatGPT features
                    has_emojis = any(char in original_response for char in "🌟🚀✅📊💡⚠️🎉")
                    has_headers = "##" in original_response
                    has_bold = "**" in original_response
                    
                    print(f"🔍 ChatGPT Features: Emojis:{has_emojis} Headers:{has_headers} Bold:{has_bold}")
                    print(f"🔧 System used: {result2.get('comprehensive_mode', 'unknown')}")
                else:
                    print(f"❌ Failed: {response.status}")
                    error = await response.text()
                    print(f"Error: {error[:200]}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("🔍 ANALYSIS:")
    print("- If both responses are different, your frontend is using the ORIGINAL endpoint")
    print("- If your app response matches #2, you need to update frontend to use /api/direct-chatgpt")
    print("- If your app response matches #1, then it's working correctly")
    
if __name__ == "__main__":
    asyncio.run(test_both_endpoints())