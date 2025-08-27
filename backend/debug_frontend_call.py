#!/usr/bin/env python3
"""Debug exactly what your frontend is calling"""

import asyncio
import aiohttp

async def debug_your_exact_call():
    """Debug the exact call your frontend makes"""
    print("🔍 DEBUGGING YOUR EXACT FRONTEND CALL")
    print("=" * 70)
    
    # Test the exact same question you're using
    url = "http://localhost:8000/api/chat/message"
    form_data = aiohttp.FormData()
    form_data.add_field('message', 'كيف يمكنني تأسيس شركة استثمار أجنبي في السعودية؟')
    form_data.add_field('session_id', 'debug_session_12345')
    
    # Try different Accept headers to see which path it takes
    test_cases = [
        {'Accept': 'application/json', 'name': 'JSON (likely frontend)'},
        {'Accept': 'text/event-stream', 'name': 'Streaming'},
        {'Accept': '*/*', 'name': 'Default'},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']} (Accept: {test_case['Accept']})")
        print("-" * 50)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form_data, headers={'Accept': test_case['Accept']}) as response:
                    if response.status == 200:
                        if test_case['Accept'] == 'text/event-stream':
                            # Handle streaming response
                            content = await response.text()
                            print("✅ Streaming response received")
                            print(f"📊 Content preview: {content[:200]}...")
                        else:
                            # Handle JSON response
                            result = await response.json()
                            ai_response = result.get("ai_message", {}).get("content", "No content")
                            
                            print("✅ JSON response received")
                            print(f"📊 Length: {len(ai_response)} chars, {len(ai_response.split())} words")
                            print("📄 Response starts with:")
                            print(f"'{ai_response[:150]}...'")
                            
                            # Check if it matches your problematic response
                            if "تأسيس شركة استثمار أجنبي في المملكة العربية السعودية يتطلب القليل من الأجراءات" in ai_response:
                                print("🚨 FOUND THE PROBLEM: This matches your bad response!")
                            elif "تمام، هاشم" in ai_response or "## 1️⃣" in ai_response:
                                print("🎉 SUCCESS: This looks like ChatGPT!")
                            else:
                                print("❓ UNKNOWN: This is a different response")
                                
                            # Check features
                            has_emojis = any(char in ai_response for char in "🌟🚀✅📊💡⚠️🎉💼🔥1️⃣2️⃣3️⃣")
                            has_headers = "##" in ai_response
                            has_personal = "هاشم" in ai_response or "تمام" in ai_response
                            
                            print(f"🔍 Features: Emojis:{has_emojis} Headers:{has_headers} Personal:{has_personal}")
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("🔍 CONCLUSION:")
    print("- If any response matches your bad response, we found the problematic path")
    print("- Check the backend logs to see which path is being taken")
    
if __name__ == "__main__":
    asyncio.run(debug_your_exact_call())