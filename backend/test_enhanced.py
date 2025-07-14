"""
Test enhanced legal system with court-specific queries
"""

import asyncio
import sys
import os

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from rag_engine import rag_engine

async def test_enhanced_system():
    """Test court-specific legal queries"""
    
    print("🧪 Testing Enhanced Legal System...")
    
    # Get current stats
    stats = await rag_engine.get_system_stats()
    print(f"📊 Current documents: {stats['total_documents']}")
    
    # Court-specific test queries
    test_queries = [
        {
            'query': 'أريد كتابة منازعة تنفيذ ضد تنفيذ حكم أجنبي',
            'expected': 'execution court template'
        },
        {
            'query': 'مذكرة جوابية في دعوى معارضة حصر إرث',
            'expected': 'family court template with fiqh'
        },
        {
            'query': 'لائحة اعتراضية على حكم إلزام برد مبلغ شيك',
            'expected': 'civil court appeal template'
        },
        {
            'query': 'استئناف على حكم جزائي بتعزير',
            'expected': 'criminal court appeal template'
        },
        {
            'query': 'ما هي حقوق العامل عند الفصل التعسفي؟',
            'expected': 'employment law consultation'
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test['query']}")
        print(f"📋 Expected: {test['expected']}")
        
        try:
            response_chunks = []
            async for chunk in rag_engine.ask_question_streaming(test['query']):
                response_chunks.append(chunk)
                if len(''.join(response_chunks)) > 500:
                    break
            
            response = ''.join(response_chunks)
            print(f"✅ Response length: {len(response)} characters")
            
            # Check for court-specific indicators
            if 'منازعة تنفيذ' in response:
                print("🎯 Detected: Execution court template")
            elif 'مذكرة جوابية' in response:
                print("🎯 Detected: Family court template")  
            elif 'لائحة اعتراضية' in response:
                print("🎯 Detected: Civil court template")
            elif 'استئناف' in response and 'جزائي' in response:
                print("🎯 Detected: Criminal court template")
            else:
                print("🎯 Detected: General consultation")
                
            print(f"📝 Sample: {response[:150]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Enhanced system test complete!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_system())