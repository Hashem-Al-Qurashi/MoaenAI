#!/usr/bin/env python3
"""Test script for ChatGPT-style comprehensive responses"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv(".env")

async def test_comprehensive_responses():
    """Test the new ChatGPT-style comprehensive mode"""
    from rag_engine import ask_question_with_context
    
    print("=" * 80)
    print("🧪 TESTING CHATGPT-STYLE COMPREHENSIVE RESPONSES")
    print("=" * 80)
    
    test_queries = [
        "ما هي حقوق الموظف في القطاع الخاص؟",
        "كيف يمكنني تأسيس شركة في السعودية؟",
        "ما هي إجراءات الطلاق في المحاكم السعودية؟"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}/{len(test_queries)}: {query}")
        print("-" * 80)
        
        try:
            # Test with comprehensive mode (default)
            response = await ask_question_with_context(
                query, 
                [],  # Empty conversation history for testing
                comprehensive_mode=True  # Explicitly set to True
            )
            
            # Analyze response
            word_count = len(response.split())
            char_count = len(response)
            
            print(f"✅ Response generated successfully!")
            print(f"📊 Statistics:")
            print(f"   - Word count: {word_count} words")
            print(f"   - Character count: {char_count} characters")
            print(f"   - Response style: {'✅ COMPREHENSIVE' if word_count > 200 else '❌ TOO SHORT'}")
            
            print(f"\n📄 Response Preview (first 500 chars):")
            print("-" * 40)
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 40)
            
            if word_count < 200:
                print("⚠️  WARNING: Response is still short. Check if AI provider is responding correctly.")
            else:
                print("🎉 SUCCESS: Response is comprehensive like ChatGPT!")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🏁 TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_comprehensive_responses())