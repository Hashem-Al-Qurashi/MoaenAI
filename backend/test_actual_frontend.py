#!/usr/bin/env python3
"""Test what the actual frontend is using"""

import asyncio
import aiohttp

async def test_frontend_path():
    """Test the exact path your frontend uses"""
    print("🔍 TESTING ACTUAL FRONTEND ENDPOINT")
    print("=" * 70)
    
    url = "http://localhost:8000/api/chat/message"
    form_data = aiohttp.FormData()
    form_data.add_field('message', 'كيف يمكنني تأسيس شركة استثمار أجنبي في السعودية؟')
    form_data.add_field('session_id', 'test_session_123')
    
    # Test with Accept: application/json (what frontend probably uses)
    headers = {
        'Accept': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_response = result.get("ai_message", {}).get("content", "No content")
                    
                    print("✅ SUCCESS!")
                    print(f"📊 Length: {len(ai_response)} chars, {len(ai_response.split())} words")
                    print("📄 Response preview (first 300 chars):")
                    print(ai_response[:300] + "...")
                    
                    # Check ChatGPT features
                    has_emojis = any(char in ai_response for char in "🌟🚀✅📊💡⚠️🎉💼🔥")
                    has_headers = "##" in ai_response
                    has_bold = "**" in ai_response
                    
                    print(f"\n🔍 ChatGPT Features:")
                    print(f"  - Emojis: {'✅' if has_emojis else '❌'}")
                    print(f"  - Headers: {'✅' if has_headers else '❌'}")
                    print(f"  - Bold: {'✅' if has_bold else '❌'}")
                    
                    if has_emojis and has_headers and has_bold:
                        print("🎉 SUCCESS: Frontend is getting ChatGPT-style responses!")
                    else:
                        print("❌ FAIL: Still not getting full ChatGPT style")
                        print(f"📝 Your current response starts with: '{ai_response[:100]}'")
                        
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    error = await response.text()
                    print(f"Error: {error}")
                    
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_path())