"""
Test script to verify integration works correctly
"""

import asyncio
import sys
import os

# Fix the path - go up one level to find the app module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now try to import
try:
    from app.rag_engine import rag_engine
    print("✅ Import successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print("Available modules:")
    for item in os.listdir('.'):
        if os.path.isdir(item):
            print(f"  📁 {item}")
    sys.exit(1)

async def test_integration():
    """Test the enhanced legal reasoning system"""
    
    print("🧪 Testing Enhanced Legal Reasoning System...")
    
    # Test queries for different court systems
    test_queries = [
        "أريد منازعة تنفيذ حكم أجنبي",  # Should trigger execution template
        "مذكرة جوابية في دعوى حصر إرث",  # Should trigger family template  
        "استئناف على حكم جزائي",  # Should trigger criminal template
        "ما هي حقوق العامل؟"  # Should trigger general consultation
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        
        try:
            # Test the streaming response
            response_chunks = []
            async for chunk in rag_engine.ask_question_streaming(query):
                response_chunks.append(chunk)
                if len(''.join(response_chunks)) > 200:  # Stop after 200 chars for testing
                    break
            
            response = ''.join(response_chunks)
            print(f"✅ Response length: {len(response)} characters")
            print(f"📝 Sample: {response[:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test system stats
    print("\n📊 System Statistics:")
    try:
        stats = await rag_engine.get_system_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    print("\n🎉 Integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_integration())