"""
Simple test - run from backend/ directory
"""

import asyncio
import sys
import os

# Add current directory to Python path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("🔍 Testing RAG Engine Import...")
print(f"Current directory: {current_dir}")

try:
    # Import the rag_engine from the main directory
    from rag_engine import rag_engine
    print("✅ Successfully imported rag_engine!")
    
    async def quick_test():
        print("\n🧪 Testing RAG Engine...")
        
        # Test query
        query = "ما هي حقوق العامل في السعودية؟"
        print(f"🔍 Testing query: {query}")
        
        try:
            response_chunks = []
            count = 0
            async for chunk in rag_engine.ask_question_streaming(query):
                response_chunks.append(chunk)
                count += 1
                if count > 10:  # Stop after 10 chunks for testing
                    break
            
            response = ''.join(response_chunks)
            print(f"✅ Success! Got {len(response)} characters in {count} chunks")
            print(f"📝 Sample response:\n{response[:200]}...")
            
        except Exception as e:
            print(f"❌ Error during streaming test: {e}")
            import traceback
            traceback.print_exc()
        
        # Test system stats
        try:
            print("\n📊 Getting system stats...")
            stats = await rag_engine.get_system_stats()
            print(f"✅ Document count: {stats.get('total_documents', 'N/A')}")
            print(f"🏥 Health status: {stats.get('health', 'N/A')}")
            print(f"🔧 AI model: {stats.get('ai_model', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
    
    # Run the test
    print("🚀 Running async test...")
    asyncio.run(quick_test())
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\n🔍 Debugging...")
    
    # Check what files we have
    print("📄 Python files in current directory:")
    for file in os.listdir('.'):
        if file.endswith('.py'):
            print(f"  📄 {file}")
    
    # Check if rag_engine.py exists
    if os.path.exists('rag_engine.py'):
        print("✅ rag_engine.py exists")
        
        # Try to check its imports
        print("🔍 Checking rag_engine.py imports...")
        with open('rag_engine.py', 'r') as f:
            first_lines = f.readlines()[:20]
            for i, line in enumerate(first_lines, 1):
                if 'import' in line:
                    print(f"  Line {i}: {line.strip()}")
    else:
        print("❌ rag_engine.py not found!")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Test complete!")